# -*- coding: utf-8 -*-
"""生成 fin 批量自动出账"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/dto/GenerateBillsCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.util.List;

/**
 * 批量自动出账。
 *
 * <p>按「生效中的合同 × 收费项目」批量生成账单。数量取值规则：
 * <ul>
 *   <li>{@code BY_AREA}：用房源面积</li>
 *   <li>{@code BY_NIGHT}：用期间天数（短租/民宿）</li>
 *   <li>{@code BY_BED} / {@code BY_PERSON}：用房源 {@code maxCapacity}，可用 {@code quantityOverride} 覆盖</li>
 *   <li>{@code FIXED} / {@code BY_HOUSE}：1</li>
 *   <li>{@code METER}：<b>不支持批量</b>（需抄表读数），会被跳过并给出原因</li>
 * </ul>
 *
 * @param dryRun true=只试算不落库，用于验证计费规则是否正确
 */
public record GenerateBillsCmd(

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        /** 可选：指定计费规则；不传则用项目默认单价 */
        Long ruleId,

        @NotNull(message = "费用起始日不能为空")
        LocalDate periodStart,
        @NotNull(message = "费用截止日不能为空")
        LocalDate periodEnd,

        /** 账期，如 2026-10；为空自动按 periodStart 生成 */
        String billPeriod,

        /** 缴费截止日；为空 = periodStart */
        LocalDate dueDate,

        /** 限定组织 */
        Long orgId,
        /** 限定房源类型（多业态） */
        String houseType,
        /** 限定合同 ID 列表（为空=全部生效合同） */
        List<Long> contractIds,

        /** 覆盖数量（BY_BED/BY_PERSON 时不按 maxCapacity） */
        Integer quantityOverride,

        /** 试运行，不落库 */
        Boolean dryRun
) {
}
'''

FILES['fin/dto/GenerateResultVO.java'] = '''package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.util.List;

/**
 * 批量出账结果。
 *
 * @param totalContracts 扫描到的生效合同数
 * @param generated      实际生成（或试算）的账单数
 * @param skipped        跳过数
 * @param skipReasons    跳过原因汇总
 * @param totalAmount    合计金额
 * @param dryRun         是否试运行
 * @param items          明细
 */
public record GenerateResultVO(
        int totalContracts,
        int generated,
        int skipped,
        List<String> skipReasons,
        BigDecimal totalAmount,
        boolean dryRun,
        List<Item> items
) {
    /**
     * @param contractId 合同
     * @param billId     生成的账单 ID（试运行时为 null）
     * @param quantity   参与计算的数量
     * @param amount     金额
     * @param explain    计算过程
     * @param status     OK / SKIPPED
     * @param reason     跳过或失败原因
     */
    public record Item(Long contractId, String contractNo, Long billId, Integer quantity,
                       BigDecimal amount, String explain, String status, String reason) {
    }
}
'''

FILES['fin/service/BillGenerationService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.fin.dto.GenerateBillsCmd;
import com.yundao.bp.fin.dto.GenerateResultVO;

/**
 * 批量自动出账服务。
 *
 * <p>把"计费引擎 + 合同 + 房源"串起来：扫描生效合同 → 逐户算费 → 生成账单 → 幂等去重。
 */
public interface BillGenerationService {

    /**
     * 批量出账。
     *
     * <p><b>幂等</b>：同「合同 + 收费项目 + 账期」已存在账单时跳过，可安全重复执行。
     */
    GenerateResultVO generate(GenerateBillsCmd cmd);
}
'''

FILES['fin/service/impl/BillGenerationServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.CalcMode;
import com.yundao.bp.fin.dto.GenerateBillsCmd;
import com.yundao.bp.fin.dto.GenerateResultVO;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.FinBillingRule;
import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinBillingRuleMapper;
import com.yundao.bp.fin.mapper.FinFeeItemMapper;
import com.yundao.bp.fin.service.BillGenerationService;
import com.yundao.bp.fin.service.BillingCalculator;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 批量自动出账实现。
 *
 * <p><b>扫描范围</b>：状态为 {@code EFFECTIVE} / {@code RENEWING} 且租期与
 * {@code [periodStart, periodEnd]} 有交集的合同。
 *
 * <p><b>数量取值</b>（多业态适配）：
 * <pre>
 *   BY_AREA  → 房源建筑面积
 *   BY_NIGHT → 期间天数（短租/民宿）
 *   BY_BED   → 房源 maxCapacity（床位数），可用 quantityOverride 覆盖
 *   BY_PERSON→ 房源 maxCapacity（可住人数），可用 quantityOverride 覆盖
 *   FIXED / BY_HOUSE → 1
 *   METER    → 跳过（需抄表读数，不能批量）
 * </pre>
 */
@Service
public class BillGenerationServiceImpl implements BillGenerationService {

    private static final Logger log = LoggerFactory.getLogger(BillGenerationServiceImpl.class);
    private static final DateTimeFormatter PERIOD_FMT = DateTimeFormatter.ofPattern("yyyy-MM");

    private final BizContractMapper contractMapper;
    private final AssetHouseMapper houseMapper;
    private final FinFeeItemMapper feeItemMapper;
    private final FinBillingRuleMapper ruleMapper;
    private final FinBillMapper billMapper;
    private final BillingCalculator calculator;
    private final SnowflakeIdGenerator idGen;

    public BillGenerationServiceImpl(BizContractMapper contractMapper,
                                     AssetHouseMapper houseMapper,
                                     FinFeeItemMapper feeItemMapper,
                                     FinBillingRuleMapper ruleMapper,
                                     FinBillMapper billMapper,
                                     BillingCalculator calculator,
                                     SnowflakeIdGenerator idGen) {
        this.contractMapper = contractMapper;
        this.houseMapper = houseMapper;
        this.feeItemMapper = feeItemMapper;
        this.ruleMapper = ruleMapper;
        this.billMapper = billMapper;
        this.calculator = calculator;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public GenerateResultVO generate(GenerateBillsCmd cmd) {
        String tenantId = TenantContext.tenantId();
        boolean dryRun = cmd.dryRun() != null && cmd.dryRun();

        FinFeeItem item = feeItemMapper.selectById(cmd.feeItemId());
        if (item == null) {
            throw BizException.notFound("收费项目");
        }
        if (!"ENABLED".equals(item.getStatus())) {
            throw BizException.stateConflict("收费项目已停用，不能出账");
        }
        CalcMode mode;
        try {
            mode = CalcMode.valueOf(item.getCalcMode());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("计费方式不合法: " + item.getCalcMode());
        }
        if (mode.needsMeter()) {
            throw BizException.stateConflict(
                    "按抄表计费（METER）不支持批量出账，请逐户录入读数后单独开单");
        }
        if (cmd.periodEnd().isBefore(cmd.periodStart())) {
            throw BizException.paramInvalid("费用截止日不能早于起始日");
        }

        FinBillingRule rule = null;
        if (cmd.ruleId() != null) {
            rule = ruleMapper.selectById(cmd.ruleId());
            if (rule == null) {
                throw BizException.notFound("计费规则");
            }
            if (!"APPROVED".equals(rule.getApproveStatus())) {
                throw BizException.stateConflict("规则未审批通过，不能用于计费");
            }
        }

        // 扫描生效合同
        LambdaQueryWrapper<BizContract> cw = new LambdaQueryWrapper<BizContract>()
                .in(BizContract::getContractStatus, List.of(
                        ContractStatus.EFFECTIVE.name(), ContractStatus.RENEWING.name()))
                .le(BizContract::getLeaseStart, cmd.periodEnd())
                .ge(BizContract::getLeaseEnd, cmd.periodStart())
                .eq(cmd.orgId() != null, BizContract::getOrgId, cmd.orgId())
                .eq(cmd.houseType() != null && !cmd.houseType().isBlank(),
                        BizContract::getContractType, cmd.houseType())
                .orderByAsc(BizContract::getId);
        if (cmd.contractIds() != null && !cmd.contractIds().isEmpty()) {
            cw.in(BizContract::getId, cmd.contractIds());
        }
        List<BizContract> contracts = contractMapper.selectList(cw);

        String billPeriod = cmd.billPeriod() == null || cmd.billPeriod().isBlank()
                ? cmd.periodStart().format(PERIOD_FMT) : cmd.billPeriod();
        LocalDate dueDate = cmd.dueDate() == null ? cmd.periodStart() : cmd.dueDate();
        int nights = (int) Math.max(1,
                ChronoUnit.DAYS.between(cmd.periodStart(), cmd.periodEnd()));

        List<GenerateResultVO.Item> items = new ArrayList<>();
        List<String> skipReasons = new ArrayList<>();
        int generated = 0;
        int skipped = 0;
        BigDecimal total = BigDecimal.ZERO;

        for (BizContract ct : contracts) {
            // 幂等：同合同+同项目+同账期已存在 → 跳过
            Long dup = billMapper.selectCount(new LambdaQueryWrapper<FinBill>()
                    .eq(FinBill::getContractId, ct.getId())
                    .eq(FinBill::getFeeItemId, cmd.feeItemId())
                    .eq(FinBill::getBillPeriod, billPeriod));
            if (dup != null && dup > 0) {
                skipped++;
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, null,
                        BigDecimal.ZERO, null, "SKIPPED", "该账期账单已存在（幂等跳过）"));
                continue;
            }

            AssetHouse house = ct.getHouseId() == null ? null
                    : houseMapper.selectById(ct.getHouseId());

            // 计算数量
            Integer qty = quantityOf(mode, house, nights, cmd.quantityOverride());
            BillingCalculator.Context ctx = contextOf(mode, house, nights, qty);
            BillingCalculator.Result rr;
            try {
                rr = calculator.calculate(item, ctx, rule);
            } catch (Exception e) {
                skipped++;
                skipReasons.add("合同 " + ct.getContractNo() + " 算费失败：" + e.getMessage());
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, qty,
                        BigDecimal.ZERO, null, "SKIPPED", e.getMessage()));
                continue;
            }

            BigDecimal amount = rr.finalAmount();
            if (amount.compareTo(BigDecimal.ZERO) <= 0) {
                skipped++;
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, qty,
                        amount, rr.explain(), "SKIPPED", "金额为 0（减免规则或数量为 0）"));
                continue;
            }

            Long billId = null;
            if (!dryRun) {
                long id = idGen.nextId();
                LocalDateTime now = LocalDateTime.now();
                FinBill b = new FinBill();
                b.setId(id);
                b.setTenantId(tenantId);
                b.setBillNo("FB" + id);
                b.setOrgId(ct.getOrgId());
                b.setContractId(ct.getId());
                b.setHouseId(ct.getHouseId());
                b.setSpaceId(ct.getSpaceId());
                b.setPersonId(ct.getLesseePersonId());
                b.setPayerName(ct.getLesseeName());
                b.setPayerPhone(ct.getLesseePhone());
                b.setFeeItemId(cmd.feeItemId());
                b.setBillPeriod(billPeriod);
                b.setPeriodStart(cmd.periodStart());
                b.setPeriodEnd(cmd.periodEnd());
                b.setBillAmount(amount);
                b.setDiscountAmount(money(null));
                b.setLateFee(money(null));
                b.setPaidAmount(money(null));
                b.setWaivedAmount(money(null));
                b.setPayableAmount(amount);
                b.setDueDate(dueDate);
                b.setBillStatus("UNPAID");
                b.setOverdueDays(0);
                b.setGenerateType("AUTO");
                b.setRemark("批量出账：" + item.getItemName());
                b.setIsDeleted(0);
                b.setCreateTime(now);
                billMapper.insert(b);
                billId = id;
            }
            generated++;
            total = total.add(amount);
            items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), billId, qty,
                    amount, rr.explain(), "OK", null));
        }

        log.info("批量出账[{}]：合同 {}，生成 {}，跳过 {}，合计 {}",
                dryRun ? "试运行" : "已落库", contracts.size(), generated, skipped, total);

        return new GenerateResultVO(contracts.size(), generated, skipped, skipReasons,
                total.setScale(2, RoundingMode.HALF_UP), dryRun, items);
    }

    /** 数量取值。 */
    private static Integer quantityOf(CalcMode mode, AssetHouse house, int nights,
                                      Integer override) {
        if (override != null && override > 0) {
            return override;
        }
        return switch (mode) {
            case BY_NIGHT -> nights;
            case BY_BED, BY_PERSON -> house != null && house.getMaxCapacity() != null
                    ? house.getMaxCapacity() : 1;
            case FIXED, BY_HOUSE, BY_AREA -> 1;
            case METER -> 1;
        };
    }

    /** 构造计算上下文。 */
    private static BillingCalculator.Context contextOf(CalcMode mode, AssetHouse house,
                                                       int nights, Integer qty) {
        return switch (mode) {
            case BY_AREA -> BillingCalculator.Context.ofArea(
                    house == null || house.getArea() == null
                            ? BigDecimal.ZERO : house.getArea());
            case BY_PERSON, BY_BED, BY_NIGHT -> BillingCalculator.Context.ofQuantity(qty);
            default -> BillingCalculator.Context.empty();
        };
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
'''

FILES['fin/controller/BillGenerationController.java'] = '''package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.GenerateBillsCmd;
import com.yundao.bp.fin.dto.GenerateResultVO;
import com.yundao.bp.fin.service.BillGenerationService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 批量自动出账接口（BC-08）。
 *
 * <p>用法：先 {@code dryRun=true} 试算核对金额，确认后 {@code dryRun=false} 落库。
 * 幂等：同「合同+收费项目+账期」已存在账单会跳过，可安全重复执行。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class BillGenerationController {

    private final BillGenerationService service;

    public BillGenerationController(BillGenerationService service) {
        this.service = service;
    }

    @PostMapping("/bills/generate")
    public R<GenerateResultVO> generate(@Valid @RequestBody GenerateBillsCmd cmd) {
        return R.ok(service.generate(cmd));
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
