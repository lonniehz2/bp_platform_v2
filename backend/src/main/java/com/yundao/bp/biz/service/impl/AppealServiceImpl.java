package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.AppealResultEffect;
import com.yundao.bp.biz.constant.AppealStatus;
import com.yundao.bp.biz.dto.AppealCreateCmd;
import com.yundao.bp.biz.dto.AppealDecisionCmd;
import com.yundao.bp.biz.dto.AppealVO;
import com.yundao.bp.biz.entity.BizAppeal;
import com.yundao.bp.biz.dto.ChangeCreateCmd;
import com.yundao.bp.biz.dto.ChangeVO;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.biz.entity.BizAnnualReview;
import com.yundao.bp.biz.entity.BizContractChange;
import com.yundao.bp.biz.mapper.BizAnnualReviewMapper;
import com.yundao.bp.biz.mapper.BizAppealMapper;
import com.yundao.bp.biz.mapper.BizContractChangeMapper;
import com.yundao.bp.biz.service.ContractChangeService;
import com.yundao.bp.biz.service.TerminationService;
import com.yundao.bp.biz.service.AppealService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.constant.ConfigKeys;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 申诉/异议实现。
 *
 * <p><b>期限控制</b>：{@code deadline_time} 之前未提出则置 {@code TIMEOUT}。
 * <b>同一业务对象同一申请人只能有一条未终结申诉</b>，防止重复申诉。
 */
@Service
public class AppealServiceImpl implements AppealService {

    private static final Logger log = LoggerFactory.getLogger(AppealServiceImpl.class);

    /** 默认申诉期限（自然日，可被系统参数覆盖） */
    private static final int DEFAULT_DAYS = 10;
    /** 系统参数（政策参数可配置） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.sys.service.ConfigService configService;

    private int cfgInt(String key, int def) {
        return configService == null ? def : configService.getInt(key, def);
    }

    private java.math.BigDecimal cfgDec(String key, String def) {
        return configService == null ? new java.math.BigDecimal(def)
                : configService.getDecimal(key, new java.math.BigDecimal(def));
    }


    private static final ObjectMapper JSON = new ObjectMapper();

    private final BizAppealMapper mapper;
    private final SnowflakeIdGenerator idGen;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private BizAnnualReviewMapper reviewMapper;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private BizContractChangeMapper changeMapper;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private ContractChangeService contractChangeService;
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private TerminationService terminationService;

    public AppealServiceImpl(BizAppealMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO submit(AppealCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        // 同业务对象 + 同申请人 只能有一条未终结申诉
        Long open = mapper.selectCount(new LambdaQueryWrapper<BizAppeal>()
                .eq(BizAppeal::getBizType, cmd.bizType())
                .eq(BizAppeal::getBizId, cmd.bizId())
                .eq(BizAppeal::getPersonId, cmd.personId())
                .in(BizAppeal::getAppealStatus, List.of(AppealStatus.SUBMITTED.name(),
                        AppealStatus.ACCEPTED.name(), AppealStatus.INVESTIGATING.name())));
        if (open != null && open > 0) {
            throw BizException.stateConflict("该业务对象已有处理中的申诉，请等待办结");
        }

        int days = cmd.daysFromNow() == null || cmd.daysFromNow() <= 0
                ? cfgInt(ConfigKeys.APPEAL_DEADLINE_DAYS, DEFAULT_DAYS)
                : cmd.daysFromNow();
        LocalDateTime now = LocalDateTime.now();
        long id = idGen.nextId();
        BizAppeal e = new BizAppeal();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setAppealNo("AP" + id);
        e.setBizType(cmd.bizType());
        e.setBizId(cmd.bizId());
        e.setPersonId(cmd.personId());
        e.setOrgId(cmd.orgId());
        e.setAppealType(cmd.appealType());
        e.setAppealReason(cmd.appealReason());
        e.setAppealEvidence(cmd.appealEvidence());
        e.setDeadlineTime(now.plusDays(days));
        e.setAppealTime(now);
        e.setAppealStatus(AppealStatus.SUBMITTED.name());
        e.setNotifyStatus("PENDING");
        e.setIsDeleted(0);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        log.info("申诉 {} 提出：{} #{}（{}），期限 {}",
                e.getAppealNo(), cmd.bizType(), cmd.bizId(),
                "OBJECTION".equals(cmd.appealType()) ? "公示异议" : "申诉", e.getDeadlineTime());
        return AppealVO.from(e);
    }

    @Override
    public AppealVO get(Long id) {
        return AppealVO.from(require(id));
    }

    @Override
    public PageResult<AppealVO> page(long pageNum, long pageSize, Long personId, String bizType,
                                     String status) {
        LambdaQueryWrapper<BizAppeal> qw = new LambdaQueryWrapper<BizAppeal>()
                .eq(personId != null, BizAppeal::getPersonId, personId)
                .eq(bizType != null && !bizType.isBlank(), BizAppeal::getBizType, bizType)
                .eq(status != null && !status.isBlank(), BizAppeal::getAppealStatus, status)
                .orderByDesc(BizAppeal::getId);
        IPage<BizAppeal> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<AppealVO> rows = page.getRecords().stream().map(AppealVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public List<AppealVO> listByBiz(String bizType, Long bizId) {
        return mapper.selectList(new LambdaQueryWrapper<BizAppeal>()
                        .eq(BizAppeal::getBizType, bizType)
                        .eq(BizAppeal::getBizId, bizId)
                        .orderByDesc(BizAppeal::getId))
                .stream().map(AppealVO::from).toList();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO accept(Long id, Long acceptUserId) {
        BizAppeal e = require(id);
        // 超过期限不可受理
        if (e.getDeadlineTime() != null && LocalDateTime.now().isAfter(e.getDeadlineTime())) {
            throw BizException.stateConflict(
                    "已超过申诉期限（" + e.getDeadlineTime() + "），不予受理");
        }
        transition(e, AppealStatus.ACCEPTED);
        e.setAcceptTime(LocalDateTime.now());
        e.setAcceptUserId(acceptUserId);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO investigate(Long id, Long handleUserId) {
        BizAppeal e = require(id);
        transition(e, AppealStatus.INVESTIGATING);
        e.setHandleUserId(handleUserId);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO decide(Long id, AppealDecisionCmd cmd) {
        BizAppeal e = require(id);
        AppealStatus target;
        try {
            target = AppealStatus.valueOf(cmd.decision());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("决定结论不合法: " + cmd.decision());
        }
        if (target != AppealStatus.UPHELD && target != AppealStatus.REJECTED) {
            throw BizException.paramInvalid("决定结论只能是 UPHELD 或 REJECTED");
        }
        AppealResultEffect re;
        try {
            re = AppealResultEffect.valueOf(cmd.resultEffect());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("结果影响不合法: " + cmd.resultEffect());
        }
        // 异议不成立却要"恢复资格"是矛盾的
        if (target == AppealStatus.REJECTED && re.changesOutcome()) {
            throw BizException.paramInvalid(
                    "异议不成立时结果影响应为 NONE（不能恢复/取消资格或调整标准）");
        }

        transition(e, target);
        e.setHandleResult(cmd.handleResult());
        e.setReviewOpinion(cmd.reviewOpinion());
        e.setResultEffect(re.name());
        e.setHandleUserId(cmd.handleUserId() == null ? e.getHandleUserId() : cmd.handleUserId());
        e.setHandleTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        // ⭐ 决定后回写原业务（决策 D29）：
        // 仅记录复议结论而不改变原决定，等于住户白申诉
        String effectNote = applyEffect(e, re, cmd);

        log.info("申诉 {} 决定：{}，影响 {}{}", e.getAppealNo(),
                target.label(), re.label(),
                effectNote == null ? "" : "；" + effectNote);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO withdraw(Long id, String reason) {
        BizAppeal e = require(id);
        transition(e, AppealStatus.WITHDRAWN);
        if (reason != null && !reason.isBlank()) {
            e.setReviewOpinion("撤回原因：" + reason);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AppealVO markNotified(Long id) {
        BizAppeal e = require(id);
        if (!appealStatusOf(e).isTerminal()) {
            throw BizException.stateConflict("申诉尚未办结，不能告知结果");
        }
        e.setNotifyStatus("SENT");
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return AppealVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int markTimeout() {
        List<BizAppeal> list = mapper.selectList(new LambdaQueryWrapper<BizAppeal>()
                .eq(BizAppeal::getAppealStatus, AppealStatus.SUBMITTED.name())
                .lt(BizAppeal::getDeadlineTime, LocalDateTime.now()));
        int n = 0;
        for (BizAppeal e : list) {
            e.setAppealStatus(AppealStatus.TIMEOUT.name());
            e.setUpdateTime(LocalDateTime.now());
            mapper.updateById(e);
            n++;
        }
        if (n > 0) {
            log.warn("申诉超期标记 {} 条", n);
        }
        return n;
    }

    /**
     * 把复议结果<b>真正落到原业务</b>上。
     *
     * <p>处理的场景：
     * <ol>
     *   <li>{@code ANNUAL_REVIEW} + {@code RESTORE}：年审结论改回「保留资格」，
     *       并把此前的调租变更<b>反向恢复</b>（按原租金再发起一笔变更，保留审计链）</li>
     *   <li>{@code EXIT} + {@code RESTORE}：撤销年审自动生成的退租腾退单</li>
     *   <li>其它组合：仅记录，需人工处置</li>
     * </ol>
     *
     * @return 处置说明（写入日志与复核意见）
     */
    private String applyEffect(BizAppeal e, AppealResultEffect re, AppealDecisionCmd cmd) {
        if (!re.changesOutcome()) {
            return null;
        }
        StringBuilder note = new StringBuilder();

        // ① 年度核查类：恢复资格 = 撤销调租 + 年审结论改 KEEP
        if ("ANNUAL_REVIEW".equals(e.getBizType()) && re == AppealResultEffect.RESTORE) {
            if (reviewMapper == null) {
                note.append("年审组件不可用，需人工恢复");
            } else {
                BizAnnualReview rv = reviewMapper.selectById(e.getBizId());
                if (rv == null) {
                    note.append("年审单不存在，需人工核实");
                } else {
                    // 反向恢复租金
                    String revert = revertRentChange(rv.getContractId());
                    if (revert != null) {
                        note.append(revert);
                    }
                    // 年审结论改回保留
                    rv.setReviewResult("KEEP");
                    rv.setAdjustContent((rv.getAdjustContent() == null ? ""
                            : rv.getAdjustContent())
                            + "｜经复议（" + e.getAppealNo() + "）异议成立，恢复原保障资格");
                    rv.setUpdateTime(LocalDateTime.now());
                    reviewMapper.updateById(rv);
                    if (note.length() > 0) {
                        note.append("；");
                    }
                    note.append("年审结论已恢复为「保留资格」");
                }
            }
        }

        // ② 退出类：撤销自动生成的退租腾退单
        if ("EXIT".equals(e.getBizType()) && re == AppealResultEffect.RESTORE) {
            String cancel = cancelAutoTermination(e);
            if (cancel != null) {
                if (note.length() > 0) {
                    note.append("；");
                }
                note.append(cancel);
            }
        }

        // ③ 其它组合：明确告知需人工
        if (note.length() == 0) {
            note.append("复议结论已记录；该业务类型（").append(e.getBizType())
                    .append("）的结果影响需人工处置");
        }

        // 把处置结果追加到复核意见，便于审计
        String op = cmd.reviewOpinion() == null ? "" : cmd.reviewOpinion();
        e.setReviewOpinion(op + "｜处置：" + note);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return note.toString();
    }

    /**
     * 反向恢复租金：找到该合同最近一笔已批准的「租金调整」，
     * 取其变更前租金，再发起一笔新变更把租金改回去。
     *
     * <p>用「再发起一笔变更」而非直接改库，是为了保留完整审计链条。
     */
    private String revertRentChange(Long contractId) {
        if (contractId == null || changeMapper == null || contractChangeService == null) {
            return null;
        }
        BizContractChange last = changeMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<BizContractChange>()
                        .eq(BizContractChange::getContractId, contractId)
                        .eq(BizContractChange::getChangeType, "RENT_ADJUST")
                        .eq(BizContractChange::getApproveStatus, "APPROVED")
                        .orderByDesc(BizContractChange::getId)
                        .last("LIMIT 1"));
        if (last == null) {
            return null;
        }
        try {
            @SuppressWarnings("unchecked")
            LinkedHashMap<String, Object> before =
                    JSON.readValue(last.getBeforeJson(), LinkedHashMap.class);
            Object oldRent = before.get("monthlyRent");
            if (oldRent == null) {
                return null;
            }
            BigDecimal rent = new BigDecimal(String.valueOf(oldRent))
                    .setScale(2, java.math.RoundingMode.HALF_UP);
            ChangeVO c = contractChangeService.create(contractId, new ChangeCreateCmd(
                    "RENT_ADJUST", "复议恢复：按原租金标准执行（来源变更单 " + last.getId() + "）",
                    rent, null, null, null, LocalDate.now(),
                    "由申诉单触发的反向调租"));
            contractChangeService.approve(c.id());
            return "租金已恢复为 " + rent + "（反向变更单 " + c.id() + "）";
        } catch (Exception ex) {
            log.warn("复议反向调租失败：{}", ex.getMessage());
            return "反向调租失败（" + ex.getMessage() + "），需人工处理";
        }
    }

    /** 撤销年审自动生成的退租腾退单。 */
    private String cancelAutoTermination(BizAppeal e) {
        if (terminationService == null || reviewMapper == null) {
            return null;
        }
        BizAnnualReview rv = reviewMapper.selectById(e.getBizId());
        if (rv == null || rv.getContractId() == null) {
            return null;
        }
        try {
            var page = terminationService.page(1, 5, null, "APPLYING", rv.getContractId(),
                    null, null);
            if (page.total() == 0) {
                return "无待处理的退租单需撤销";
            }
            TerminationVO t = page.rows().get(0);
            terminationService.cancel(t.id(),
                    "复议（" + e.getAppealNo() + "）异议成立，撤销腾退决定");
            return "已撤销退租单 " + t.terminationNo();
        } catch (Exception ex) {
            log.warn("撤销退租单失败：{}", ex.getMessage());
            return "撤销退租单失败（" + ex.getMessage() + "），需人工处理";
        }
    }

    // ==================== 内部 ====================

    private BizAppeal require(Long id) {
        BizAppeal e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("申诉单");
        }
        return e;
    }

    private static AppealStatus appealStatusOf(BizAppeal e) {
        try {
            return AppealStatus.valueOf(e.getAppealStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("申诉状态非法: " + e.getAppealStatus());
        }
    }

    private static void transition(BizAppeal e, AppealStatus target) {
        AppealStatus from = appealStatusOf(e);
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!AppealStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "申诉状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setAppealStatus(target.name());
    }
}
