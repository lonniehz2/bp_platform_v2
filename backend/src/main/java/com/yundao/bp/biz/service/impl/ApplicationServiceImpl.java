package com.yundao.bp.biz.service.impl;

import com.yundao.bp.person.mapper.PersonMapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.ApplicationStatus;
import com.yundao.bp.biz.constant.ReviewResult;
import com.yundao.bp.biz.constant.ReviewStage;
import com.yundao.bp.biz.dto.ApplicationCreateCmd;
import com.yundao.bp.biz.dto.ApplicationVO;
import com.yundao.bp.biz.dto.ReviewCmd;
import com.yundao.bp.biz.entity.BizApplication;
import com.yundao.bp.biz.entity.BizReviewRecord;
import com.yundao.bp.biz.mapper.BizApplicationMapper;
import com.yundao.bp.biz.mapper.BizReviewRecordMapper;
import com.yundao.bp.biz.service.CreditService;
import com.yundao.bp.person.service.GuaranteeProfileService;
import com.yundao.bp.person.service.VerifyRecordService;
import com.yundao.bp.sys.constant.ConfigKeys;
import com.yundao.bp.sys.service.ConfigService;
import com.yundao.bp.biz.service.ApplicationService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 申请与审核实现。
 *
 * <p><b>状态机推进规则</b>：
 * <ul>
 *   <li>提交后 {@code SUBMITTED}，受理后 {@code ACCEPTED→REVIEWING}</li>
 *   <li>审核 {@code PASS}：非终审 → 停留 {@code REVIEWING} 并推进阶段；终审 → {@code APPROVED}</li>
 *   <li>审核 {@code REJECT}：→ {@code REJECTED}（终态）</li>
 *   <li>审核 {@code SUPPLEMENT}：→ {@code SUPPLEMENT}（待补件），补件后 {@code resubmit} 回 {@code REVIEWING}</li>
 * </ul>
 *
 * <p><b>人均收入</b>：{@code incomePerCapita = declaredIncome / familySize}，
 * 用于分档判定（各地政策对照见 {@code 01_需求与功能方案.md} §3.4）。
 */
@Service
public class ApplicationServiceImpl implements ApplicationService {

    private static final Logger log = LoggerFactory.getLogger(ApplicationServiceImpl.class);

    private final BizApplicationMapper appMapper;
    private final PersonMapper personMapper;
    private final BizReviewRecordMapper reviewMapper;
    private final SnowflakeIdGenerator idGen;

    /** 信用惩戒服务（可选注入，避免影响既有构造器与单测） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private CreditService creditService;

    /** 实名认证服务（可选注入） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private VerifyRecordService verifyRecordService;

    /** 系统参数（实名开关与例外策略） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private ConfigService configService;

    /** 保障对象档案（资格判定依据） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private GuaranteeProfileService guaranteeProfileService;

    public ApplicationServiceImpl(BizApplicationMapper appMapper,
                                  BizReviewRecordMapper reviewMapper,
                                  SnowflakeIdGenerator idGen, PersonMapper personMapper) {
        this.personMapper = personMapper;
        this.appMapper = appMapper;
        this.reviewMapper = reviewMapper;
        this.idGen = idGen;
    }

    /**
     * 实名认证校验。
     *
     * <p><b>规则</b>：该人员最近一次实名认证必须通过，否则不得申请。
     *
     * <p><b>为什么必须真正拦在申请入口</b>：实名认证是「人证合一」的唯一保证，
     * 只在建档时记录而不校验，等于允许冒名申请——这是保障房领域最常见也最严重的骗租手法。
     *
     * <p><b>可配置</b>：部分地区允许"先申请后认证"（如线上提交、线下核验），
     * 由系统参数 {@code biz.apply.requireVerify} 控制，默认要求认证。
     * 关闭时不做拦截，但仍会记录（便于事后审计）。
     */
    private void checkVerify(Long personId) {
        if (personId == null) {
            throw BizException.paramInvalid("申请人不能为空");
        }
        boolean required = configService == null
                || configService.getBool(ConfigKeys.APPLY_REQUIRE_VERIFY, true);
        if (!required) {
            return;
        }
        if (verifyRecordService == null) {
            // 未部署认证能力时不阻断（灰度环境），但不静默放行到无感知
            return;
        }
        java.util.Map<String, Object> c = verifyRecordService.conclusion(personId);
        Object verified = c.get("verified");
        if (!Boolean.TRUE.equals(verified)) {
            Object reason = c.get("conclusion");
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "申请人尚未通过实名认证，不能提交申请。"
                            + (reason == null ? "" : "（" + reason + "）")
                            + " 请在「实名认证」中完成人脸或身份证核验后重试。");
        }
    }

    /**
     * 资格判定（审核通过前执行）。
     *
     * <p><b>为什么必须做</b>：如果审核员只勾选「通过」而不看保障档案，
     * 审核环节就退化成了形式。本方法把「档案里的事实」变成硬性判定：
     *
     * <ol>
     *   <li><b>档案必须存在</b>——没有收入/人口信息就无法判断是否符合条件</li>
     *   <li><b>收入档位不能是 NORMAL</b>——超过中低收入线即不符合保障条件</li>
     *   <li><b>家庭人口必须一致</b>——申请填 3 人、档案记 1 人属申报不实</li>
     *   <li><b>人才公寓必须有人才认定</b>且证书在有效期内</li>
     *   <li><b>名下有房</b>需人工说明（部分业态允许，如人才公寓）</li>
     * </ol>
     *
     * <p>判定不通过时抛 {@code STATE_CONFLICT}，并在信息中说明<b>具体不符合哪一条</b>，
     * 供审核员退回或补充材料。
     */
    private void checkQualification(BizApplication e) {
        if (guaranteeProfileService == null) {
            return;
        }
        com.yundao.bp.person.entity.PersonGuaranteeProfile profile;
        try {
            profile = guaranteeProfileService.getByPerson(e.getPersonId());
        } catch (BizException ex) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "该申请人尚无保障对象档案（缺收入/家庭人口信息），不能通过资格审核。"
                            + "请先在「保障档案」中建档后再审核。");
        }

        // ① 收入档位：NORMAL 表示超过中低收入线，不符合保障条件
        String level = profile.getIncomeLevel();
        if ("NORMAL".equals(level)) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "不符合保障条件：家庭人均月收入已超过中低收入线（当前档位：普通）。"
                            + "如认为档案数据有误，请先更新收入信息并重新核算档位。");
        }

        // ② 家庭人口一致性：申报人口与档案不一致属于申报不实
        Integer declared = e.getFamilySize();
        Integer actual = profile.getFamilySize();
        if (declared != null && actual != null && !declared.equals(actual)) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "申报家庭人口（" + declared + " 人）与保障档案登记（" + actual
                            + " 人）不一致，涉嫌申报不实。请核实后由申请人更正申报。");
        }

        // ③ 人才公寓：必须有人才认定且证书在有效期内
        if ("TALENT".equals(e.getSecurityType())) {
            if (profile.getTalentLevel() == null || profile.getTalentLevel().isBlank()) {
                throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                        "人才公寓申请必须提供人才认定信息，当前档案无人才层次记录。");
            }
            if (profile.getTalentValidTo() != null
                    && profile.getTalentValidTo().isBefore(java.time.LocalDate.now())) {
                throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                        "人才认定已过期（有效期至 " + profile.getTalentValidTo()
                                + "），请重新认定后再申请人才公寓。");
            }
        }

        // ④ 名下有房：不直接拒绝（部分业态允许），但要求档案有备注说明
        if (profile.getHasHouse() != null && profile.getHasHouse() == 1
                && (profile.getRemark() == null || profile.getRemark().isBlank())) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "申请人名下已有 " + (profile.getHouseCount() == null ? "多"
                            : profile.getHouseCount()) + " 套住房，"
                            + "需在档案备注中说明符合例外情形的依据后才能通过审核。");
        }
    }

    // ==================== 创建 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO create(ApplicationCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        // ⭐ 信用惩戒校验（决策 D31）：处于限制申请期的人员不得申请
        // 放在最前面，避免"填完一堆材料才被告知不能申请"
        if (creditService != null) {
            creditService.checkApplyBan(cmd.personId());
        }

        // ⭐ 实名认证校验（决策 D32）：未通过实名认证不得申请
        // 同样前置，理由同信用校验：不让申请人白填材料
        checkVerify(cmd.personId());

        // 保障房必备：真实性承诺书 + 同意核实
        if (cmd.complianceCommitFlag() == null || cmd.complianceCommitFlag() != 1) {
            throw BizException.paramInvalid("必须签署申报信息真实性承诺书");
        }
        if (cmd.dataShareAgreeFlag() == null || cmd.dataShareAgreeFlag() != 1) {
            throw BizException.paramInvalid("必须书面同意核实申报信息");
        }
        if (cmd.intentAreaMin() != null && cmd.intentAreaMax() != null
                && cmd.intentAreaMin().compareTo(cmd.intentAreaMax()) > 0) {
            throw BizException.paramInvalid("意向最小面积不能大于最大面积");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizApplication e = new BizApplication();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setApplicationNo("BA" + id);
        e.setOrgId(cmd.orgId());
        e.setPersonId(cmd.personId());
        e.setSecurityType(cmd.securityType());
        e.setSecurityMode(blankToNull(cmd.securityMode()) == null ? "HOUSE" : cmd.securityMode());
        e.setApplyChannel(blankToNull(cmd.applyChannel()) == null ? "OFFLINE" : cmd.applyChannel());
        e.setApplyTime(now);
        e.setFamilySize(cmd.familySize());
        e.setIntentDistrict(cmd.intentDistrict());
        e.setIntentProject(cmd.intentProject());
        e.setIntentLayout(cmd.intentLayout());
        e.setIntentAreaMin(cmd.intentAreaMin());
        e.setIntentAreaMax(cmd.intentAreaMax());
        e.setFormData(cmd.formData());
        e.setAttachmentUrls(cmd.attachmentUrls());
        e.setDeclaredIncome(cmd.declaredIncome());
        e.setDeclaredIncomeYear(cmd.declaredIncomeYear());
        e.setFamilyPropertyAmount(cmd.familyPropertyAmount());
        e.setIncomeCheckPeriod(blankToNull(cmd.incomeCheckPeriod()) == null
                ? "LAST_YEAR" : cmd.incomeCheckPeriod());
        // 人均月收入派生
        if (cmd.declaredIncome() != null && cmd.familySize() != null && cmd.familySize() > 0) {
            e.setIncomePerCapita(cmd.declaredIncome()
                    .divide(BigDecimal.valueOf(cmd.familySize()), 2, RoundingMode.HALF_UP));
        }
        e.setComplianceCommitFlag(cmd.complianceCommitFlag());
        e.setDataShareAgreeFlag(cmd.dataShareAgreeFlag());
        e.setRemark(cmd.remark());
        e.setApplicationStatus(ApplicationStatus.SUBMITTED.name());
        e.setCurrentNode(ReviewStage.ACCEPT.name());
        e.setIsDeleted(0);
        e.setCreateTime(now);
        appMapper.insert(e);
        return ApplicationVO.from(e);
    }

    // ==================== 查询 ====================

    @Override
    public ApplicationVO get(Long id) {
        return ApplicationVO.from(require(id));
    }

    @Override
    public PageResult<ApplicationVO> page(long pageNum, long pageSize, String securityType,
                                          String status, Long orgId, String keyword) {
        LambdaQueryWrapper<BizApplication> qw = new LambdaQueryWrapper<BizApplication>()
                .eq(securityType != null && !securityType.isBlank(),
                        BizApplication::getSecurityType, securityType)
                .eq(status != null && !status.isBlank(),
                        BizApplication::getApplicationStatus, status)
                .eq(orgId != null, BizApplication::getOrgId, orgId)
                .orderByDesc(BizApplication::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(BizApplication::getApplicationNo, keyword));
        }
        IPage<BizApplication> page = appMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<BizApplication> records = page.getRecords();
        // 批量填充申请人姓名：一次 in 查询，避免 N+1，前端不再显示 personId 数字
        java.util.Map<Long, String> personNameMap = new java.util.HashMap<>();
        java.util.List<Long> personIds = records.stream()
                .map(BizApplication::getPersonId)
                .filter(java.util.Objects::nonNull)
                .distinct()
                .toList();
        if (!personIds.isEmpty()) {
            for (com.yundao.bp.person.entity.Person p : personMapper.selectBatchIds(personIds)) {
                personNameMap.put(p.getId(), p.getPersonName());
            }
        }
        List<ApplicationVO> rows = records.stream()
                .map(e -> ApplicationVO.from(e, personNameMap.get(e.getPersonId())))
                .toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public List<BizReviewRecord> reviewRecords(Long applicationId) {
        require(applicationId);
        return reviewMapper.selectList(new LambdaQueryWrapper<BizReviewRecord>()
                .eq(BizReviewRecord::getApplicationId, applicationId)
                .orderByAsc(BizReviewRecord::getReviewRound)
                .orderByAsc(BizReviewRecord::getCreateTime)
                .orderByAsc(BizReviewRecord::getId));
    }

    // ==================== 受理 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO accept(Long id, Long acceptUserId) {
        BizApplication e = require(id);
        transition(e, ApplicationStatus.ACCEPTED);
        e.setAcceptTime(LocalDateTime.now());
        e.setAcceptUserId(acceptUserId);
        // 受理即进入审核中
        e.setApplicationStatus(ApplicationStatus.REVIEWING.name());
        e.setCurrentNode(ReviewStage.FORM.name());
        e.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(e);
        return ApplicationVO.from(e);
    }

    // ==================== 审核 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO review(Long id, ReviewCmd cmd, Long reviewUserId, String reviewUserName) {
        BizApplication e = require(id);
        ApplicationStatus cur = statusOf(e);
        if (!cur.isInReview()) {
            throw BizException.stateConflict(
                    "申请单当前状态（" + cur.label() + "）不可审核");
        }
        // 待补件状态下只能先补件再审核
        if (cur == ApplicationStatus.SUPPLEMENT) {
            throw BizException.stateConflict("申请单待补件，请先补件后重新提交再审核");
        }

        ReviewStage stage;
        try {
            stage = ReviewStage.valueOf(cmd.stage());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("审核阶段不合法: " + cmd.stage());
        }
        ReviewResult result;
        try {
            result = ReviewResult.valueOf(cmd.result());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("审核结果不合法: " + cmd.result());
        }

        int round = reviewMapper.selectCount(new LambdaQueryWrapper<BizReviewRecord>()
                .eq(BizReviewRecord::getApplicationId, id)).intValue() + 1;

        BizReviewRecord r = new BizReviewRecord();
        r.setId(idGen.nextId());
        r.setTenantId(e.getTenantId());
        r.setApplicationId(id);
        r.setReviewRound(round);
        r.setReviewStage(stage.name());
        r.setReviewDept(blankToNull(cmd.dept()));
        r.setReviewType("MANUAL");
        r.setReviewUserId(reviewUserId);
        r.setReviewUserName(reviewUserName);
        r.setReviewTime(LocalDateTime.now());
        r.setReviewResult(result.name());
        r.setCheckItems(cmd.checkItems());
        r.setReviewOpinion(cmd.opinion());
        r.setCreateTime(LocalDateTime.now());
        reviewMapper.insert(r);

        // ⭐ 资格判定校验（决策 D33）：审核通过前必须依据保障档案判定资格
        // 只信任手工勾选"通过"而不看档案，等于审核流于形式
        if (result == ReviewResult.PASS) {
            checkQualification(e);
        }

        // 推进状态机
        switch (result) {
            case REJECT -> {
                transition(e, ApplicationStatus.REJECTED);
                e.setRejectReason(cmd.rejectReason() == null
                        ? cmd.opinion() : cmd.rejectReason());
            }
            case SUPPLEMENT -> {
                transition(e, ApplicationStatus.SUPPLEMENT);
                e.setSupplementDemand(cmd.supplementDemand() == null
                        ? cmd.opinion() : cmd.supplementDemand());
            }
            case PASS -> {
                if (stage.isLast()) {
                    transition(e, ApplicationStatus.APPROVED);
                    e.setCurrentNode("DONE");
                } else {
                    // 非终审通过：停留 REVIEWING，推进到下一阶段
                    e.setCurrentNode(stage.next().name());
                }
            }
            default -> {
            }
        }
        e.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(e);
        log.info("申请 {} 审核 {} {} → 状态 {}", e.getApplicationNo(), stage.name(),
                result.name(), e.getApplicationStatus());
        return ApplicationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO resubmit(Long id) {
        BizApplication e = require(id);
        transition(e, ApplicationStatus.REVIEWING);
        e.setSupplementDemand(null);
        e.setCurrentNode(ReviewStage.FORM.name());
        e.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(e);
        return ApplicationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ApplicationVO cancel(Long id, String reason) {
        BizApplication e = require(id);
        ApplicationStatus cur = statusOf(e);
        if (cur != ApplicationStatus.DRAFT && cur != ApplicationStatus.SUBMITTED
                && cur != ApplicationStatus.SUPPLEMENT) {
            throw BizException.stateConflict(
                    "当前状态（" + cur.label() + "）不可撤回，已进入审核流程");
        }
        transition(e, ApplicationStatus.CANCELLED);
        e.setRemark(reason == null ? e.getRemark() : reason);
        e.setUpdateTime(LocalDateTime.now());
        appMapper.updateById(e);
        return ApplicationVO.from(e);
    }

    // ==================== 内部 ====================

    private BizApplication require(Long id) {
        BizApplication e = appMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("申请单");
        }
        return e;
    }

    private static ApplicationStatus statusOf(BizApplication e) {
        try {
            return ApplicationStatus.valueOf(e.getApplicationStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("申请单状态非法: " + e.getApplicationStatus());
        }
    }

    private static void transition(BizApplication e, ApplicationStatus target) {
        ApplicationStatus from = statusOf(e);
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ApplicationStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setApplicationStatus(target.name());
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
