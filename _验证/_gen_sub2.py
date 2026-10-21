# -*- coding: utf-8 -*-
"""生成 fin 补贴标准与发放（第二部分：服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/service/SubsidyService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.SubsidyCalcCmd;
import com.yundao.bp.fin.dto.SubsidyGrantCmd;
import com.yundao.bp.fin.dto.SubsidyRecordVO;
import com.yundao.bp.fin.dto.SubsidyStandardCreateCmd;
import com.yundao.bp.fin.dto.SubsidyStandardVO;
import java.math.BigDecimal;
import java.util.List;

/**
 * 补贴标准与发放服务（广州"实物配租 + 租赁补贴"双轨支撑）。
 *
 * <p><b>计算口径</b>：
 * <pre>
 *   FIXED    → 金额 = 补贴值
 *   BY_AREA  → 金额 = 单价 × 面积
 *   BY_PERSON→ 金额 = 人均 × 人口
 *   RATIO    → 金额 = 月租金 × 比例
 *   最后统一受 max_amount 封顶
 * </pre>
 */
public interface SubsidyService {

    // ---------- 标准 ----------
    SubsidyStandardVO createStandard(SubsidyStandardCreateCmd cmd);

    SubsidyStandardVO getStandard(Long id);

    PageResult<SubsidyStandardVO> pageStandards(long pageNum, long pageSize, String securityType,
                                                String subsidyMode, String keyword);

    SubsidyStandardVO setStandardStatus(Long id, boolean enabled);

    /** 试算（不落库）。 */
    SubsidyCalcResult preview(SubsidyCalcCmd cmd);

    // ---------- 发放 ----------
    /** 单户单期发放（自动匹配标准、算金额、建记录）。 */
    SubsidyRecordVO grant(SubsidyGrantCmd cmd);

    SubsidyRecordVO getRecord(Long id);

    PageResult<SubsidyRecordVO> pageRecords(long pageNum, long pageSize, Long contractId,
                                            Long personId, String period, String status);

    /** 批量发放：按期间对全部生效合同（实物配租之外的补贴对象）发放。 */
    BatchResult grantBatch(String subsidyPeriod, Long orgId, String payMode, boolean dryRun);

    /** 确认发放成功（联动：OFFSET_RENT 方式会自动抵扣当期租金账单）。 */
    SubsidyRecordVO confirmPaid(Long id, BigDecimal paidAmount, String financeBatchNo);

    /** 标记发放失败。 */
    SubsidyRecordVO markFailed(Long id, String failReason);

    /** 试算结果。 */
    record SubsidyCalcResult(Long standardId, String standardCode, String subsidyMode,
                             BigDecimal amount, BigDecimal cappedAmount, boolean capped,
                             String explain) {
    }

    /** 批量结果。 */
    record BatchResult(String subsidyPeriod, int total, int granted, int skipped,
                       BigDecimal totalAmount, boolean dryRun, List<String> skipReasons) {
    }
}
'''

FILES['fin/service/impl/SubsidyServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.BillStatus;
import com.yundao.bp.fin.constant.SubsidyMode;
import com.yundao.bp.fin.constant.SubsidyStatus;
import com.yundao.bp.fin.dto.SubsidyCalcCmd;
import com.yundao.bp.fin.dto.SubsidyGrantCmd;
import com.yundao.bp.fin.dto.SubsidyRecordVO;
import com.yundao.bp.fin.dto.SubsidyStandardCreateCmd;
import com.yundao.bp.fin.dto.SubsidyStandardVO;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.FinSubsidyRecord;
import com.yundao.bp.fin.entity.FinSubsidyStandard;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinSubsidyRecordMapper;
import com.yundao.bp.fin.mapper.FinSubsidyStandardMapper;
import com.yundao.bp.fin.service.SubsidyService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 补贴标准与发放实现。
 *
 * <p><b>补贴计算</b>（{@link SubsidyMode}）：
 * <pre>
 *   FIXED     = 补贴值
 *   BY_AREA   = 单价 × 面积
 *   BY_PERSON = 人均 × 家庭人口
 *   RATIO     = 月租金 × 比例
 *   → 统一受 max_amount 月度封顶
 * </pre>
 *
 * <p><b>发放方式 OFFSET_RENT（抵扣租金）</b>：确认发放时自动核销当期租金账单，
 * 减免额＝补贴额；补贴不足以覆盖账单时账单转为部分缴。
 */
@Service
public class SubsidyServiceImpl implements SubsidyService {

    private static final Logger log = LoggerFactory.getLogger(SubsidyServiceImpl.class);

    private final FinSubsidyStandardMapper standardMapper;
    private final FinSubsidyRecordMapper recordMapper;
    private final FinBillMapper billMapper;
    private final BizContractMapper contractMapper;
    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;

    public SubsidyServiceImpl(FinSubsidyStandardMapper standardMapper,
                              FinSubsidyRecordMapper recordMapper,
                              FinBillMapper billMapper,
                              BizContractMapper contractMapper,
                              AssetHouseMapper houseMapper,
                              SnowflakeIdGenerator idGen) {
        this.standardMapper = standardMapper;
        this.recordMapper = recordMapper;
        this.billMapper = billMapper;
        this.contractMapper = contractMapper;
        this.houseMapper = houseMapper;
        this.idGen = idGen;
    }

    // ==================== 标准 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SubsidyStandardVO createStandard(SubsidyStandardCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        Long dup = standardMapper.selectCount(new LambdaQueryWrapper<FinSubsidyStandard>()
                .eq(FinSubsidyStandard::getStandardCode, cmd.standardCode()));
        if (dup != null && dup > 0) {
            throw new BizException(ErrorCode.DUPLICATED,
                    "补贴标准编码已存在: " + cmd.standardCode());
        }
        SubsidyMode mode;
        try {
            mode = SubsidyMode.valueOf(cmd.subsidyMode());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("补贴方式不合法: " + cmd.subsidyMode());
        }
        // RATIO 比例不能超过 1（100%）
        if (mode == SubsidyMode.RATIO
                && cmd.subsidyValue().compareTo(BigDecimal.ONE) > 0) {
            throw BizException.paramInvalid("按租金比例补贴时，比例不能超过 1（即 100%）");
        }
        if (cmd.effectiveStart() != null && cmd.effectiveEnd() != null
                && !cmd.effectiveEnd().isAfter(cmd.effectiveStart())) {
            throw BizException.paramInvalid("生效结束日必须晚于开始日");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinSubsidyStandard e = new FinSubsidyStandard();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setStandardCode(cmd.standardCode());
        e.setStandardName(cmd.standardName());
        e.setSecurityType(cmd.securityType());
        e.setOrgId(cmd.orgId());
        e.setIncomeLevel(cmd.incomeLevel());
        e.setFamilyType(cmd.familyType());
        e.setTalentLevel(cmd.talentLevel());
        e.setSubsidyMode(mode.name());
        e.setSubsidyValue(cmd.subsidyValue());
        e.setMaxAmount(cmd.maxAmount() == null ? null : money(cmd.maxAmount()));
        e.setEffectiveStart(cmd.effectiveStart() == null ? LocalDate.now()
                : cmd.effectiveStart());
        e.setEffectiveEnd(cmd.effectiveEnd());
        e.setStatus("ENABLED");
        e.setIsDeleted(0);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        standardMapper.insert(e);
        return SubsidyStandardVO.from(e);
    }

    @Override
    public SubsidyStandardVO getStandard(Long id) {
        FinSubsidyStandard e = standardMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("补贴标准");
        }
        return SubsidyStandardVO.from(e);
    }

    @Override
    public PageResult<SubsidyStandardVO> pageStandards(long pageNum, long pageSize,
                                                       String securityType, String subsidyMode,
                                                       String keyword) {
        LambdaQueryWrapper<FinSubsidyStandard> qw = new LambdaQueryWrapper<FinSubsidyStandard>()
                .eq(securityType != null && !securityType.isBlank(),
                        FinSubsidyStandard::getSecurityType, securityType)
                .eq(subsidyMode != null && !subsidyMode.isBlank(),
                        FinSubsidyStandard::getSubsidyMode, subsidyMode)
                .orderByDesc(FinSubsidyStandard::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(FinSubsidyStandard::getStandardName, keyword)
                    .or().like(FinSubsidyStandard::getStandardCode, keyword));
        }
        IPage<FinSubsidyStandard> page = standardMapper.selectPage(
                new Page<>(pageNum, pageSize), qw);
        List<SubsidyStandardVO> rows = page.getRecords().stream()
                .map(SubsidyStandardVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SubsidyStandardVO setStandardStatus(Long id, boolean enabled) {
        FinSubsidyStandard e = standardMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("补贴标准");
        }
        e.setStatus(enabled ? "ENABLED" : "DISABLED");
        e.setUpdateTime(LocalDateTime.now());
        standardMapper.updateById(e);
        return SubsidyStandardVO.from(e);
    }

    @Override
    public SubsidyCalcResult preview(SubsidyCalcCmd cmd) {
        BizContract ct = contractMapper.selectById(cmd.contractId());
        if (ct == null) {
            throw BizException.notFound("合同");
        }
        FinSubsidyStandard std = resolveStandard(cmd.standardId(), ct);
        return calc(std, ct, cmd.area(), cmd.personCount(), cmd.monthlyRent());
    }

    // ==================== 发放 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SubsidyRecordVO grant(SubsidyGrantCmd cmd) {
        String tenantId = TenantContext.tenantId();
        BizContract ct = contractMapper.selectById(cmd.contractId());
        if (ct == null) {
            throw BizException.notFound("合同");
        }
        // 幂等：同合同+同期间只发一次
        Long dup = recordMapper.selectCount(new LambdaQueryWrapper<FinSubsidyRecord>()
                .eq(FinSubsidyRecord::getContractId, cmd.contractId())
                .eq(FinSubsidyRecord::getSubsidyPeriod, cmd.subsidyPeriod()));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict(
                    "该合同 " + cmd.subsidyPeriod() + " 补贴已发放（幂等拒绝）");
        }

        FinSubsidyStandard std = resolveStandard(cmd.standardId(), ct);
        SubsidyCalcResult r = calc(std, ct, null, null, null);
        if (r.cappedAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.stateConflict("按当前标准计算补贴为 0，无法发放");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinSubsidyRecord e = new FinSubsidyRecord();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setRecordNo("FS" + id);
        e.setStandardId(std.getId());
        e.setContractId(ct.getId());
        e.setPersonId(cmd.personId());
        e.setPersonName(ct.getLesseeName());
        e.setOrgId(ct.getOrgId());
        e.setSubsidyPeriod(cmd.subsidyPeriod());
        e.setSubsidyAmount(r.cappedAmount());
        e.setPaidAmount(money(null));
        e.setPayMode(cmd.payMode() == null || cmd.payMode().isBlank()
                ? "FINANCE" : cmd.payMode());
        e.setBankAccount(cmd.bankAccount());
        e.setRecordStatus(SubsidyStatus.PENDING.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        recordMapper.insert(e);
        log.info("补贴发放登记：合同 {} 期间 {} 应发 {}（标准 {}：{}）",
                ct.getContractNo(), cmd.subsidyPeriod(), r.cappedAmount(),
                std.getStandardCode(), r.explain());
        return SubsidyRecordVO.from(e);
    }

    @Override
    public SubsidyRecordVO getRecord(Long id) {
        return SubsidyRecordVO.from(requireRecord(id));
    }

    @Override
    public PageResult<SubsidyRecordVO> pageRecords(long pageNum, long pageSize, Long contractId,
                                                   Long personId, String period, String status) {
        LambdaQueryWrapper<FinSubsidyRecord> qw = new LambdaQueryWrapper<FinSubsidyRecord>()
                .eq(contractId != null, FinSubsidyRecord::getContractId, contractId)
                .eq(personId != null, FinSubsidyRecord::getPersonId, personId)
                .eq(period != null && !period.isBlank(),
                        FinSubsidyRecord::getSubsidyPeriod, period)
                .eq(status != null && !status.isBlank(),
                        FinSubsidyRecord::getRecordStatus, status)
                .orderByDesc(FinSubsidyRecord::getId);
        IPage<FinSubsidyRecord> page = recordMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<SubsidyRecordVO> rows = page.getRecords().stream()
                .map(SubsidyRecordVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BatchResult grantBatch(String subsidyPeriod, Long orgId, String payMode,
                                  boolean dryRun) {
        YearMonth ym;
        try {
            ym = YearMonth.parse(subsidyPeriod);
        } catch (Exception e) {
            throw BizException.paramInvalid("补贴期间格式应为 YYYY-MM");
        }
        LocalDate ps = ym.atDay(1);
        LocalDate pe = ym.atEndOfMonth();

        List<BizContract> contracts = contractMapper.selectList(
                new LambdaQueryWrapper<BizContract>()
                        .in(BizContract::getContractStatus, List.of(
                                ContractStatus.EFFECTIVE.name(),
                                ContractStatus.RENEWING.name()))
                        .le(BizContract::getLeaseStart, pe)
                        .ge(BizContract::getLeaseEnd, ps)
                        .eq(orgId != null, BizContract::getOrgId, orgId)
                        .orderByAsc(BizContract::getId));

        int granted = 0;
        int skipped = 0;
        BigDecimal total = BigDecimal.ZERO;
        List<String> skipReasons = new ArrayList<>();

        for (BizContract ct : contracts) {
            try {
                // 幂等检查
                Long dup = recordMapper.selectCount(new LambdaQueryWrapper<FinSubsidyRecord>()
                        .eq(FinSubsidyRecord::getContractId, ct.getId())
                        .eq(FinSubsidyRecord::getSubsidyPeriod, subsidyPeriod));
                if (dup != null && dup > 0) {
                    skipped++;
                    skipReasons.add("合同 " + ct.getContractNo() + "：" + subsidyPeriod
                            + " 已发放（幂等跳过）");
                    continue;
                }
                FinSubsidyStandard std;
                try {
                    std = resolveStandard(null, ct);
                } catch (BizException be) {
                    skipped++;
                    skipReasons.add("合同 " + ct.getContractNo() + "：" + be.getMessage());
                    continue;
                }
                SubsidyCalcResult r = calc(std, ct, null, null, null);
                if (r.cappedAmount().compareTo(BigDecimal.ZERO) <= 0) {
                    skipped++;
                    skipReasons.add("合同 " + ct.getContractNo() + "：按标准计算补贴为 0");
                    continue;
                }
                if (!dryRun) {
                    long id = idGen.nextId();
                    LocalDateTime now = LocalDateTime.now();
                    FinSubsidyRecord e = new FinSubsidyRecord();
                    e.setId(id);
                    e.setTenantId(TenantContext.tenantId());
                    e.setRecordNo("FS" + id);
                    e.setStandardId(std.getId());
                    e.setContractId(ct.getId());
                    e.setPersonId(ct.getLesseePersonId());
                    e.setPersonName(ct.getLesseeName());
                    e.setOrgId(ct.getOrgId());
                    e.setSubsidyPeriod(subsidyPeriod);
                    e.setSubsidyAmount(r.cappedAmount());
                    e.setPaidAmount(money(null));
                    e.setPayMode(payMode == null || payMode.isBlank() ? "FINANCE" : payMode);
                    e.setRecordStatus(SubsidyStatus.PENDING.name());
                    e.setCreateTime(now);
                    e.setUpdateTime(now);
                    recordMapper.insert(e);
                }
                granted++;
                total = total.add(r.cappedAmount());
            } catch (Exception ex) {
                skipped++;
                skipReasons.add("合同 " + ct.getContractNo() + " 失败：" + ex.getMessage());
            }
        }
        log.info("补贴批量发放[{}]：期间 {} 合同 {} 发放 {} 跳过 {} 合计 {}",
                dryRun ? "试运行" : "已落库", subsidyPeriod, contracts.size(), granted,
                skipped, total);
        return new BatchResult(subsidyPeriod, contracts.size(), granted, skipped,
                total.setScale(2, RoundingMode.HALF_UP), dryRun, skipReasons);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SubsidyRecordVO confirmPaid(Long id, BigDecimal paidAmount, String financeBatchNo) {
        FinSubsidyRecord e = requireRecord(id);
        SubsidyStatus from = statusOf(e);
        if (from == SubsidyStatus.SUCCESS) {
            throw BizException.stateConflict("补贴已发放");
        }
        if (from == SubsidyStatus.RETURNED) {
            throw BizException.stateConflict("补贴已退回，不可发放");
        }
        BigDecimal paid = paidAmount == null ? money(e.getSubsidyAmount()) : money(paidAmount);
        if (paid.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("实发金额必须大于 0");
        }
        if (paid.compareTo(money(e.getSubsidyAmount())) > 0) {
            throw BizException.paramInvalid(
                    "实发金额不能超过应发金额 " + money(e.getSubsidyAmount()));
        }

        e.setPaidAmount(paid);
        e.setRecordStatus(SubsidyStatus.SUCCESS.name());
        e.setIssueDate(LocalDate.now());
        if (financeBatchNo != null) {
            e.setFinanceBatchNo(financeBatchNo);
        }
        e.setUpdateTime(LocalDateTime.now());
        recordMapper.updateById(e);

        // OFFSET_RENT 抵扣租金：直接冲减当期租金账单
        if ("OFFSET_RENT".equals(e.getPayMode())) {
            int offset = offsetRent(e.getContractId(), e.getSubsidyPeriod(), paid);
            log.info("补贴 {} 抵扣租金 {}：冲减 {} 张账单", e.getRecordNo(), paid, offset);
        }
        return SubsidyRecordVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SubsidyRecordVO markFailed(Long id, String failReason) {
        FinSubsidyRecord e = requireRecord(id);
        SubsidyStatus from = statusOf(e);
        if (from.isTerminal()) {
            throw BizException.stateConflict("补贴已" + from.label() + "，不可改为失败");
        }
        e.setRecordStatus(SubsidyStatus.FAILED.name());
        e.setFailReason(failReason);
        e.setUpdateTime(LocalDateTime.now());
        recordMapper.updateById(e);
        return SubsidyRecordVO.from(e);
    }

    // ==================== 计算 ====================

    /** 按标准与合同算补贴。 */
    private SubsidyCalcResult calc(FinSubsidyStandard std, BizContract ct, BigDecimal areaIn,
                                   Integer personIn, BigDecimal rentIn) {
        SubsidyMode mode;
        try {
            mode = SubsidyMode.valueOf(std.getSubsidyMode());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("补贴方式不合法: " + std.getSubsidyMode());
        }
        BigDecimal value = std.getSubsidyValue() == null ? BigDecimal.ZERO : std.getSubsidyValue();

        BigDecimal area = areaIn;
        if (area == null && ct.getHouseId() != null) {
            AssetHouse h = houseMapper.selectById(ct.getHouseId());
            area = h == null ? null : h.getArea();
        }
        BigDecimal rent = rentIn == null ? ct.getMonthlyRent() : rentIn;
        int persons = personIn == null || personIn <= 0
                ? (ct.getCohabitantCount() == null || ct.getCohabitantCount() <= 0
                ? 1 : ct.getCohabitantCount()) : personIn;

        BigDecimal amount;
        String explain;
        switch (mode) {
            case FIXED -> {
                amount = value;
                explain = "定额 " + value + " 元/月";
            }
            case BY_AREA -> {
                if (area == null || area.compareTo(BigDecimal.ZERO) <= 0) {
                    throw BizException.stateConflict(
                            "按面积补贴需房源面积，但合同 " + ct.getContractNo()
                                    + " 未录入面积（houseId=" + ct.getHouseId() + "）");
                }
                amount = value.multiply(area);
                explain = "按面积 " + value + " 元/㎡·月 × " + area + "㎡";
            }
            case BY_PERSON -> {
                amount = value.multiply(BigDecimal.valueOf(persons));
                explain = "按人 " + value + " 元/人·月 × " + persons + " 人";
            }
            case RATIO -> {
                BigDecimal r = rent == null ? BigDecimal.ZERO : rent;
                amount = r.multiply(value);
                explain = "按租金比例 " + value + " × 月租 " + r;
            }
            default -> throw BizException.paramInvalid("补贴方式不合法");
        }
        amount = amount.setScale(2, RoundingMode.HALF_UP);

        // 封顶
        boolean capped = false;
        BigDecimal finalAmount = amount;
        if (std.getMaxAmount() != null && amount.compareTo(std.getMaxAmount()) > 0) {
            finalAmount = money(std.getMaxAmount());
            capped = true;
            explain = explain + " → 封顶 " + finalAmount;
        }
        return new SubsidyCalcResult(std.getId(), std.getStandardCode(), mode.name(),
                amount, finalAmount, capped, explain);
    }

    /** 匹配补贴标准：指定 > 按合同类型+组织 > 按合同类型。 */
    private FinSubsidyStandard resolveStandard(Long standardId, BizContract ct) {
        if (standardId != null) {
            FinSubsidyStandard s = standardMapper.selectById(standardId);
            if (s == null) {
                throw BizException.notFound("补贴标准");
            }
            if (!"ENABLED".equals(s.getStatus())) {
                throw BizException.stateConflict("补贴标准已停用");
            }
            return s;
        }
        // 合同类型 → 保障类型映射（PUBLIC_RENTAL→PUBLIC 等）
        String securityType = mapSecurityType(ct.getContractType());
        LocalDate today = LocalDate.now();

        List<FinSubsidyStandard> list = standardMapper.selectList(
                new LambdaQueryWrapper<FinSubsidyStandard>()
                        .eq(FinSubsidyStandard::getStatus, "ENABLED")
                        .eq(FinSubsidyStandard::getSecurityType, securityType)
                        .le(FinSubsidyStandard::getEffectiveStart, today)
                        .and(w -> w.isNull(FinSubsidyStandard::getEffectiveEnd)
                                .or().ge(FinSubsidyStandard::getEffectiveEnd, today))
                        .orderByDesc(FinSubsidyStandard::getId));
        if (list.isEmpty()) {
            throw BizException.stateConflict(
                    "未找到保障类型 " + securityType + " 的启用补贴标准");
        }
        // 优先取限定本组织的
        for (FinSubsidyStandard s : list) {
            if (s.getOrgId() != null && s.getOrgId().equals(ct.getOrgId())) {
                return s;
            }
        }
        // 再取通用（orgId 为空）
        for (FinSubsidyStandard s : list) {
            if (s.getOrgId() == null) {
                return s;
            }
        }
        return list.get(0);
    }

    private static String mapSecurityType(String contractType) {
        if (contractType == null) {
            return "PUBLIC";
        }
        return switch (contractType) {
            case "PUBLIC_RENTAL" -> "PUBLIC";
            case "AFFORDABLE" -> "AFFORDABLE";
            case "TALENT" -> "TALENT";
            case "LOW_RENT" -> "LOW_RENT";
            default -> "PUBLIC";
        };
    }

    /**
     * 补贴抵扣租金：冲减该合同当期租金账单。
     *
     * <p>按账期匹配账单，逐张核销直到补贴额用尽；不足全额时账单转 PARTIAL。
     */
    private int offsetRent(Long contractId, String subsidyPeriod, BigDecimal amount) {
        List<FinBill> bills = billMapper.selectList(new LambdaQueryWrapper<FinBill>()
                .eq(FinBill::getContractId, contractId)
                .eq(FinBill::getBillPeriod, subsidyPeriod)
                .in(FinBill::getBillStatus, List.of(BillStatus.UNPAID.name(),
                        BillStatus.PARTIAL.name(), BillStatus.OVERDUE.name()))
                .orderByAsc(FinBill::getDueDate));
        BigDecimal remain = money(amount);
        int n = 0;
        for (FinBill b : bills) {
            if (remain.compareTo(BigDecimal.ZERO) <= 0) {
                break;
            }
            BigDecimal payable = money(b.getPayableAmount());
            if (payable.compareTo(BigDecimal.ZERO) <= 0) {
                continue;
            }
            BigDecimal use = remain.min(payable);
            b.setWaivedAmount(money(b.getWaivedAmount()).add(use)
                    .setScale(2, RoundingMode.HALF_UP));
            BigDecimal newPayable = payable.subtract(use).setScale(2, RoundingMode.HALF_UP);
            b.setPayableAmount(newPayable);
            b.setBillStatus(newPayable.compareTo(BigDecimal.ZERO) <= 0
                    ? BillStatus.PAID.name() : BillStatus.PARTIAL.name());
            b.setUpdateTime(LocalDateTime.now());
            billMapper.updateById(b);
            remain = remain.subtract(use);
            n++;
        }
        return n;
    }

    private FinSubsidyRecord requireRecord(Long id) {
        FinSubsidyRecord e = recordMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("补贴发放记录");
        }
        return e;
    }

    private static SubsidyStatus statusOf(FinSubsidyRecord e) {
        try {
            return SubsidyStatus.valueOf(e.getRecordStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("补贴记录状态非法: " + e.getRecordStatus());
        }
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
'''

FILES['fin/controller/SubsidyController.java'] = '''package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.SubsidyCalcCmd;
import com.yundao.bp.fin.dto.SubsidyGrantCmd;
import com.yundao.bp.fin.dto.SubsidyRecordVO;
import com.yundao.bp.fin.dto.SubsidyStandardCreateCmd;
import com.yundao.bp.fin.dto.SubsidyStandardVO;
import com.yundao.bp.fin.service.SubsidyService;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 补贴标准与发放接口（BC-08，广州双轨支撑）。
 */
@RestController
@RequestMapping("/api/v1/fin/subsidies")
public class SubsidyController {

    private final SubsidyService service;

    public SubsidyController(SubsidyService service) {
        this.service = service;
    }

    // ---------- 标准 ----------

    @PostMapping("/standards")
    public R<SubsidyStandardVO> createStandard(@Valid @RequestBody SubsidyStandardCreateCmd cmd) {
        return R.ok(service.createStandard(cmd));
    }

    @GetMapping("/standards/{id}")
    public R<SubsidyStandardVO> getStandard(@PathVariable Long id) {
        return R.ok(service.getStandard(id));
    }

    @GetMapping("/standards")
    public R<PageResult<SubsidyStandardVO>> pageStandards(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String securityType,
            @RequestParam(required = false) String subsidyMode,
            @RequestParam(required = false) String keyword) {
        return R.ok(service.pageStandards(pageNum, pageSize, securityType, subsidyMode, keyword));
    }

    @PostMapping("/standards/{id}/status")
    public R<SubsidyStandardVO> setStatus(@PathVariable Long id,
                                          @RequestBody StatusCmd cmd) {
        return R.ok(service.setStandardStatus(id, cmd.enabled()));
    }

    /** 补贴试算（不落库）。 */
    @PostMapping("/calc")
    public R<SubsidyService.SubsidyCalcResult> calc(@Valid @RequestBody SubsidyCalcCmd cmd) {
        return R.ok(service.preview(cmd));
    }

    // ---------- 发放 ----------

    @PostMapping("/records")
    public R<SubsidyRecordVO> grant(@Valid @RequestBody SubsidyGrantCmd cmd) {
        return R.ok(service.grant(cmd));
    }

    @GetMapping("/records/{id}")
    public R<SubsidyRecordVO> getRecord(@PathVariable Long id) {
        return R.ok(service.getRecord(id));
    }

    @GetMapping("/records")
    public R<PageResult<SubsidyRecordVO>> pageRecords(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long contractId,
            @RequestParam(required = false) Long personId,
            @RequestParam(required = false) String period,
            @RequestParam(required = false) String status) {
        return R.ok(service.pageRecords(pageNum, pageSize, contractId, personId, period, status));
    }

    /** 批量发放。 */
    @PostMapping("/records/batch")
    public R<SubsidyService.BatchResult> grantBatch(@RequestBody BatchCmd cmd) {
        return R.ok(service.grantBatch(cmd.subsidyPeriod(), cmd.orgId(), cmd.payMode(),
                cmd.dryRun() != null && cmd.dryRun()));
    }

    /** 确认发放（OFFSET_RENT 会抵扣当期租金账单）。 */
    @PostMapping("/records/{id}/confirm")
    public R<SubsidyRecordVO> confirm(@PathVariable Long id, @RequestBody(required = false) ConfirmCmd cmd) {
        return R.ok(service.confirmPaid(id, cmd == null ? null : cmd.paidAmount(),
                cmd == null ? null : cmd.financeBatchNo()));
    }

    /** 标记发放失败。 */
    @PostMapping("/records/{id}/fail")
    public R<SubsidyRecordVO> fail(@PathVariable Long id,
                                   @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.markFailed(id, cmd == null ? null : cmd.reason()));
    }

    public record StatusCmd(boolean enabled) {
    }

    public record BatchCmd(String subsidyPeriod, Long orgId, String payMode, Boolean dryRun) {
    }

    public record ConfirmCmd(BigDecimal paidAmount, String financeBatchNo) {
    }

    public record ReasonCmd(String reason) {
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('生成 %d 个文件' % count)
