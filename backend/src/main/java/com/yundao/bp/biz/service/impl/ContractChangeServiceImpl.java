package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.bp.biz.constant.ApproveStatus;
import com.yundao.bp.biz.constant.ChangeType;
import com.yundao.bp.biz.dto.ChangeCreateCmd;
import com.yundao.bp.biz.dto.ChangeVO;
import com.yundao.bp.biz.entity.BizAnnualReview;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizContractChange;
import com.yundao.bp.biz.mapper.BizAnnualReviewMapper;
import com.yundao.bp.biz.mapper.BizContractChangeMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.biz.service.ContractChangeService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 合同变更实现。
 *
 * <p><b>审计</b>：每次变更都把变更前后关键字段存 JSON，任何调价都可追溯。
 */
@Service
public class ContractChangeServiceImpl implements ContractChangeService {

    private static final Logger log = LoggerFactory.getLogger(ContractChangeServiceImpl.class);
    private static final ObjectMapper JSON = new ObjectMapper();

    private final BizContractChangeMapper mapper;
    private final BizContractMapper contractMapper;
    private final BizAnnualReviewMapper reviewMapper;
    private final SnowflakeIdGenerator idGen;

    public ContractChangeServiceImpl(BizContractChangeMapper mapper,
                                     BizContractMapper contractMapper,
                                     BizAnnualReviewMapper reviewMapper,
                                     SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.contractMapper = contractMapper;
        this.reviewMapper = reviewMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ChangeVO create(Long contractId, ChangeCreateCmd cmd) {
        BizContract ct = requireContract(contractId);
        ChangeType type;
        try {
            type = ChangeType.valueOf(cmd.changeType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("变更类型不合法: " + cmd.changeType());
        }

        // 按类型校验必填
        if (type == ChangeType.RENT_ADJUST) {
            if (cmd.newMonthlyRent() == null
                    || cmd.newMonthlyRent().compareTo(BigDecimal.ZERO) <= 0) {
                throw BizException.paramInvalid("租金调整必须填写新租金（大于 0）");
            }
            if (cmd.newMonthlyRent().compareTo(ct.getMonthlyRent()) == 0) {
                throw BizException.paramInvalid(
                        "新租金与当前租金相同（" + ct.getMonthlyRent() + "），无需变更");
            }
        }
        if (type == ChangeType.PERIOD) {
            if (cmd.newLeaseEnd() == null) {
                throw BizException.paramInvalid("租期变更必须填写新止租日");
            }
            if (!cmd.newLeaseEnd().isAfter(ct.getLeaseStart())) {
                throw BizException.paramInvalid("新止租日必须晚于起租日");
            }
        }
        if (type == ChangeType.LESSEE && cmd.newLesseePersonId() == null) {
            throw BizException.paramInvalid("承租人变更必须填写新承租人人员ID");
        }
        // 同一合同不允许有多个待审批变更
        Long pending = mapper.selectCount(new LambdaQueryWrapper<BizContractChange>()
                .eq(BizContractChange::getContractId, contractId)
                .eq(BizContractChange::getApproveStatus, ApproveStatus.PENDING.name()));
        if (pending != null && pending > 0) {
            throw BizException.stateConflict("该合同已有待审批的变更，请先处理");
        }

        Map<String, Object> before = snapshot(ct);
        Map<String, Object> after = new LinkedHashMap<>(before);
        if (cmd.newMonthlyRent() != null) {
            after.put("monthlyRent", money(cmd.newMonthlyRent()));
        }
        if (cmd.newLeaseEnd() != null) {
            after.put("leaseEnd", cmd.newLeaseEnd().toString());
        }
        if (cmd.newLesseePersonId() != null) {
            after.put("lesseePersonId", cmd.newLesseePersonId());
            after.put("lesseeName", cmd.newLesseeName());
        }
        if (cmd.remark() != null) {
            after.put("remark", cmd.remark());
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizContractChange e = new BizContractChange();
        e.setId(id);
        e.setTenantId(TenantContext.tenantId());
        e.setContractId(contractId);
        e.setChangeType(type.name());
        e.setChangeReason(cmd.changeReason());
        e.setBeforeJson(toJson(before));
        e.setAfterJson(toJson(after));
        e.setApproveStatus(ApproveStatus.PENDING.name());
        e.setEffectiveDate(cmd.effectiveDate());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        log.info("合同 {} 发起{}：{}", ct.getContractNo(), type.label(), cmd.changeReason());
        return ChangeVO.from(e);
    }

    @Override
    public ChangeVO get(Long id) {
        return ChangeVO.from(requireChange(id));
    }

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;

    private ChangeVO enrichChange(ChangeVO v) {
        if (v == null || jdbc == null) {
            return v;
        }
        String houseName = null;
        String lesseeName = null;
        try {
            java.util.List<java.util.Map<String, Object>> rows = jdbc.queryForList(
                    "select h.house_name, c.lessee_name from bp_biz_contract c "
                            + "left join bp_asset_house h on h.id = c.house_id "
                            + "where c.id = ?", v.contractId());
            if (!rows.isEmpty()) {
                houseName = (String) rows.get(0).get("house_name");
                lesseeName = (String) rows.get(0).get("lessee_name");
            }
        } catch (Exception ignore) {
        }
        return new ChangeVO(v.id(), v.changeNo(), v.contractId(), v.newContractId(),
                v.changeType(), v.changeTypeLabel(), v.changeReason(), v.beforeJson(),
                v.afterJson(), v.approveStatus(), v.approveStatusLabel(), v.effectiveDate(),
                v.createTime(), houseName, lesseeName, null);
    }

    @Override
    public PageResult<ChangeVO> page(long pageNum, long pageSize, Long contractId,
                                     String changeType, String status) {
        LambdaQueryWrapper<BizContractChange> qw = new LambdaQueryWrapper<BizContractChange>()
                .eq(contractId != null, BizContractChange::getContractId, contractId)
                .eq(changeType != null && !changeType.isBlank(),
                        BizContractChange::getChangeType, changeType)
                .eq(status != null && !status.isBlank(),
                        BizContractChange::getApproveStatus, status)
                .orderByDesc(BizContractChange::getId);
        IPage<BizContractChange> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ChangeVO> rows = page.getRecords().stream().map(ChangeVO::from).map(this::enrichChange).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ChangeVO approve(Long id) {
        BizContractChange e = requireChange(id);
        transition(e, ApproveStatus.APPROVED);

        BizContract ct = requireContract(e.getContractId());
        Map<String, Object> after = fromJson(e.getAfterJson());

        ChangeType type;
        try {
            type = ChangeType.valueOf(e.getChangeType());
        } catch (IllegalArgumentException ex) {
            type = ChangeType.OTHER;
        }

        // 未到生效日：先记批准，等定时任务到期写回
        java.time.LocalDate eff = e.getEffectiveDate() == null
                ? java.time.LocalDate.now() : e.getEffectiveDate();
        if (eff.isAfter(java.time.LocalDate.now())) {
            e.setApproveStatus(ApproveStatus.APPROVED.name());
            e.setApplied(0);
            e.setUpdateTime(LocalDateTime.now());
            mapper.updateById(e);
            log.info("变更单 {} 已批准，生效日 {}，到期自动写回", id, eff);
            return ChangeVO.from(e);
        }
        applyToContract(ct, after);

        // ⭐ 真正写回合同
        if (false && after.containsKey("monthlyRent")) {
            BigDecimal newRent = new BigDecimal(String.valueOf(after.get("monthlyRent")))
                    .setScale(2, RoundingMode.HALF_UP);
            log.info("合同 {} 租金调整：{} → {}", ct.getContractNo(), ct.getMonthlyRent(),
                    newRent);
            ct.setMonthlyRent(newRent);
        }
        if (after.containsKey("leaseEnd")) {
            LocalDate newEnd = LocalDate.parse(String.valueOf(after.get("leaseEnd")));
            log.info("合同 {} 止租日变更：{} → {}", ct.getContractNo(), ct.getLeaseEnd(), newEnd);
            ct.setLeaseEnd(newEnd);
        }
        if (after.containsKey("lesseePersonId")) {
            Long pid = Long.valueOf(String.valueOf(after.get("lesseePersonId")));
            log.info("合同 {} 承租人变更：{} → {}", ct.getContractNo(), ct.getLesseePersonId(),
                    pid);
            ct.setLesseePersonId(pid);
            Object nm = after.get("lesseeName");
            if (nm != null) {
                ct.setLesseeName(String.valueOf(nm));
            }
        }
        ct.setUpdateTime(LocalDateTime.now());
        contractMapper.updateById(ct);

        e.setApproveStatus(ApproveStatus.APPROVED.name());
        e.setApplied(1);
        if (e.getEffectiveDate() == null) {
            e.setEffectiveDate(LocalDate.now());
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("变更单 {} 已批准并写回合同", id);
        return ChangeVO.from(e);
    }

    /** 把变更内容写回合同（批准且到生效日时调用）。 */
    private void applyToContract(BizContract ct, Map<String, Object> after) {
        if (after.containsKey("monthlyRent")) {
            BigDecimal newRent = new BigDecimal(String.valueOf(after.get("monthlyRent")))
                    .setScale(2, RoundingMode.HALF_UP);
            log.info("合同 {} 租金调整：{} → {}", ct.getContractNo(), ct.getMonthlyRent(), newRent);
            ct.setMonthlyRent(newRent);
            if (ct.getSubsidyAmount() != null) {
                ct.setActualPay(newRent.subtract(ct.getSubsidyAmount())
                        .setScale(2, RoundingMode.HALF_UP));
            }
        }
        if (after.containsKey("leaseEnd")) {
            ct.setLeaseEnd(LocalDate.parse(String.valueOf(after.get("leaseEnd"))));
        }
        if (after.containsKey("lesseePersonId")) {
            ct.setLesseePersonId(Long.valueOf(String.valueOf(after.get("lesseePersonId"))));
            Object nm = after.get("lesseeName");
            if (nm != null) {
                ct.setLesseeName(String.valueOf(nm));
            }
        }
        ct.setUpdateTime(LocalDateTime.now());
        contractMapper.updateById(ct);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ChangeVO reject(Long id, String reason) {
        BizContractChange e = requireChange(id);
        transition(e, ApproveStatus.REJECTED);
        if (reason != null && !reason.isBlank()) {
            e.setChangeReason((e.getChangeReason() == null ? "" : e.getChangeReason())
                    + "｜驳回原因：" + reason);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ChangeVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ChangeVO createFromReview(Long reviewId, BigDecimal newMonthlyRent, String reason) {
        BizAnnualReview rv = reviewMapper.selectById(reviewId);
        if (rv == null) {
            throw BizException.notFound("年审单");
        }
        if (rv.getContractId() == null) {
            throw BizException.stateConflict("该年审单未关联合同，无法发起变更");
        }
        // 年审结果必须是"调整"才可发起调租
        if (!"ADJUST".equals(rv.getReviewResult())) {
            throw BizException.stateConflict(
                    "年审结论为「" + rv.getReviewResult() + "」，仅「ADJUST 调整」可发起调租变更");
        }
        ChangeCreateCmd cmd = new ChangeCreateCmd("RENT_ADJUST",
                reason == null || reason.isBlank()
                        ? "年审结论调租（年审单 " + rv.getReviewNo() + "）" : reason,
                newMonthlyRent, null, null, null, LocalDate.now(),
                "来源：年审 " + rv.getReviewNo() + "｜" + rv.getAdjustContent());
        return create(rv.getContractId(), cmd);
    }

    // ==================== 内部 ====================

    private static Map<String, Object> snapshot(BizContract ct) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("contractNo", ct.getContractNo());
        m.put("monthlyRent", ct.getMonthlyRent() == null ? null : money(ct.getMonthlyRent()));
        m.put("subsidyAmount", ct.getSubsidyAmount());
        m.put("leaseStart", ct.getLeaseStart() == null ? null : ct.getLeaseStart().toString());
        m.put("leaseEnd", ct.getLeaseEnd() == null ? null : ct.getLeaseEnd().toString());
        m.put("lesseePersonId", ct.getLesseePersonId());
        m.put("lesseeName", ct.getLesseeName());
        return m;
    }

    private BizContract requireContract(Long id) {
        BizContract e = contractMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("合同");
        }
        return e;
    }

    private BizContractChange requireChange(Long id) {
        BizContractChange e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("变更单");
        }
        return e;
    }

    private static void transition(BizContractChange e, ApproveStatus target) {
        ApproveStatus from;
        try {
            from = ApproveStatus.valueOf(e.getApproveStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("变更单状态非法: " + e.getApproveStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ApproveStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "变更单状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setApproveStatus(target.name());
    }

    private static String toJson(Map<String, Object> m) {
        try {
            return JSON.writeValueAsString(m);
        } catch (Exception e) {
            return "{}";
        }
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> fromJson(String s) {
        try {
            if (s == null || s.isBlank()) {
                return new LinkedHashMap<>();
            }
            return JSON.readValue(s, LinkedHashMap.class);
        } catch (Exception e) {
            return new LinkedHashMap<>();
        }
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
