package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizContractCohabitant;
import com.yundao.bp.biz.mapper.BizContractCohabitantMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.CalcMode;
import com.yundao.bp.fin.dto.GenerateBatchCmd;
import com.yundao.bp.fin.dto.GenerateBatchVO;
import com.yundao.bp.fin.dto.GenerateBillsCmd;
import com.yundao.bp.fin.dto.GenerateResultVO;
import com.yundao.bp.fin.dto.RecalcBillsCmd;
import com.yundao.bp.fin.dto.RecalcBillsResult;
import com.yundao.bp.fin.dto.BillExplainVO;
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
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.LinkedHashMap;
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
    private static final String SKIPPED_LITERAL = "SKIPPED";

    private final BizContractMapper contractMapper;
    private final AssetHouseMapper houseMapper;
    private final FinFeeItemMapper feeItemMapper;
    private final FinBillingRuleMapper ruleMapper;
    private final FinBillMapper billMapper;
    private final BizContractCohabitantMapper cohabitantMapper;
    private final BillingCalculator calculator;
    private final SnowflakeIdGenerator idGen;

    public BillGenerationServiceImpl(BizContractMapper contractMapper,
                                     AssetHouseMapper houseMapper,
                                     FinFeeItemMapper feeItemMapper,
                                     FinBillingRuleMapper ruleMapper,
                                     FinBillMapper billMapper,
                                     BizContractCohabitantMapper cohabitantMapper,
                                     BillingCalculator calculator,
                                     SnowflakeIdGenerator idGen) {
        this.contractMapper = contractMapper;
        this.houseMapper = houseMapper;
        this.feeItemMapper = feeItemMapper;
        this.ruleMapper = ruleMapper;
        this.billMapper = billMapper;
        this.cohabitantMapper = cohabitantMapper;
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
        // 长租/固定费用账单必须按自然月出账，禁止一张账单跨两个自然月；
        // 首月、末月、调租月通过租期/费用区间交集在本月内折算。
        if (!java.time.YearMonth.from(cmd.periodStart())
                .equals(java.time.YearMonth.from(cmd.periodEnd()))) {
            throw BizException.paramInvalid(
                    "账单不能跨自然月，请按自然月分别生成（如 2026-11-01~2026-11-30）");
        }

        String ruleMode = cmd.ruleMode() == null || cmd.ruleMode().isBlank()
                ? (cmd.ruleId() != null ? "MANUAL" : "AUTO")
                : cmd.ruleMode().trim().toUpperCase();
        if (!List.of("AUTO", "MANUAL", "NONE").contains(ruleMode)) {
            throw BizException.paramInvalid("规则方式不合法: " + cmd.ruleMode());
        }
        FinBillingRule manualRule = null;
        if ("MANUAL".equals(ruleMode)) {
            if (cmd.ruleId() == null) {
                throw BizException.paramInvalid("指定规则时必须选择计费规则");
            }
            manualRule = ruleMapper.selectById(cmd.ruleId());
            if (manualRule == null) {
                throw BizException.notFound("计费规则");
            }
            if (!"APPROVED".equals(manualRule.getApproveStatus())) {
                throw BizException.stateConflict("规则未审批通过，不能用于计费");
            }
        }
        // 自动匹配候选：只取本项目、已启用、已审批的规则
        List<FinBillingRule> candidates = new ArrayList<>();
        if ("AUTO".equals(ruleMode)) {
            candidates = ruleMapper.selectList(new LambdaQueryWrapper<FinBillingRule>()
                    .eq(FinBillingRule::getFeeItemId, cmd.feeItemId())
                    .eq(FinBillingRule::getStatus, "ENABLED")
                    .eq(FinBillingRule::getApproveStatus, "APPROVED")
                    .eq(FinBillingRule::getIsDeleted, 0));
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

        String billPeriod = normalizePeriod(cmd.billPeriod(), cmd.periodStart());
        // 默认付款到期日取“生成月月末”；跨月补账/预收场景由调用方显式传入实际到期日。
        LocalDate dueDate = cmd.dueDate() == null
                ? LocalDate.now().with(java.time.temporal.TemporalAdjusters.lastDayOfMonth())
                : cmd.dueDate();
        int nights = (int) Math.max(1,
                ChronoUnit.DAYS.between(cmd.periodStart(), cmd.periodEnd()));

        List<GenerateResultVO.Item> items = new ArrayList<>();
        List<String> skipReasons = new ArrayList<>();
        int generated = 0;
        int skipped = 0;
        BigDecimal total = BigDecimal.ZERO;

        for (BizContract ct : contracts) {
            // 幂等：同合同+同项目，账期相同或费用区间有重叠 → 跳过，避免重复收费
            final LocalDate ps = cmd.periodStart();
            final LocalDate pe = cmd.periodEnd();
            Long dup = billMapper.selectCount(new LambdaQueryWrapper<FinBill>()
                    .eq(FinBill::getContractId, ct.getId())
                    .eq(FinBill::getFeeItemId, cmd.feeItemId())
                    .eq(FinBill::getIsDeleted, 0)
                    .and(w -> w.eq(FinBill::getBillPeriod, billPeriod)
                            .or(o -> o.le(FinBill::getPeriodStart, pe)
                                    .ge(FinBill::getPeriodEnd, ps))));
            if (dup != null && dup > 0) {
                skipped++;
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, null,
                        BigDecimal.ZERO, null, "SKIPPED",
                        "该合同在本账期或重叠区间已有账单（幂等跳过）"));
                continue;
            }

            AssetHouse house = ct.getHouseId() == null ? null
                    : houseMapper.selectById(ct.getHouseId());
            FinBillingRule effectiveRule = "NONE".equals(ruleMode) ? null
                    : ("MANUAL".equals(ruleMode) ? manualRule
                    : matchRule(candidates, ct, house, cmd.periodStart(), cmd.periodEnd()));

            // 计算数量
            // 按面积计费但房源未录面积：明确跳过并给出准确原因，
            // 不能兜底成 0 再以"金额为 0"跳过（原因会误导排查）
            if (mode.needsArea() && (house == null || house.getArea() == null
                    || house.getArea().compareTo(BigDecimal.ZERO) <= 0)) {
                skipped++;
                String why = house == null ? "合同未关联房源"
                        : "房源未录入建筑面积（houseId=" + house.getId() + "）";
                skipReasons.add("合同 " + ct.getContractNo() + " 跳过：" + why);
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, null,
                        BigDecimal.ZERO, null, SKIPPED_LITERAL, why));
                continue;
            }

            Integer qty = quantityOf(mode, ct, house, nights, cmd.quantityOverride());
            // 期间与合同交集的按天折算（整月=1；不足月/跨月按月内天数占比）
            Proration pro = proration(ct, cmd.periodStart(), cmd.periodEnd());
            BillingCalculator.Context ctx = contextOf(mode, house, nights, qty)
                    .withMonths(pro.months());

            // 租金类项目：以合同月租为准，不再套用收费项目里的默认单价；
            // 合同月补贴作为减免，账单应收=月租×月数，减免=补贴×月数，待缴=差额。
            BigDecimal amount;
            BigDecimal discount = money(null);
            String calcExplain;
            BigDecimal unitPriceSnapshot = item.getUnitPrice();
            String priceSource = "FEE_ITEM";
            // 仅“整套/面积/固定”租金用合同月租覆盖；
            // 按人/按床/按夜的租金项目按收费项目单价×数量，不能套整间月租
            if ("RENT".equals(item.getItemType())
                    && ct.getMonthlyRent() != null
                    && ct.getMonthlyRent().compareTo(BigDecimal.ZERO) > 0
                    && (mode == CalcMode.BY_HOUSE || mode == CalcMode.BY_AREA
                        || mode == CalcMode.FIXED)) {
                amount = money(ct.getMonthlyRent().multiply(pro.months()));
                unitPriceSnapshot = ct.getMonthlyRent();
                priceSource = "CONTRACT_RENT";
                calcExplain = "合同月租 " + ct.getMonthlyRent().toPlainString()
                        + " × " + pro.months().stripTrailingZeros().toPlainString() + " 个月";
                // 合同租金仍受规则约束：EXEMPT 归零、DISCOUNT 打折
                BigDecimal adjusted = calculator.applyRuleToAmount(amount, effectiveRule);
                if (adjusted.compareTo(amount) != 0) {
                    calcExplain = calcExplain + "；规则调整后 " + adjusted.toPlainString();
                    amount = money(adjusted);
                }
            } else {
                BillingCalculator.Result rr;
                try {
                    rr = calculator.calculate(item, ctx, effectiveRule);
                } catch (Exception e) {
                    skipped++;
                    skipReasons.add("合同 " + ct.getContractNo() + " 算费失败：" + e.getMessage());
                    items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, qty,
                            BigDecimal.ZERO, null, "SKIPPED", e.getMessage()));
                    continue;
                }
                amount = rr.finalAmount();
                calcExplain = rr.explain();
            }

            BigDecimal payable = amount.subtract(discount);
            if (amount.compareTo(BigDecimal.ZERO) <= 0) {
                skipped++;
                items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), null, qty,
                        amount, calcExplain, "SKIPPED", "金额为 0（减免规则或数量为 0）"));
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
                b.setSettlementDate(cmd.periodEnd());
                b.setBillAmount(amount);
                b.setUnitPriceSnapshot(unitPriceSnapshot);
                b.setPriceSource(priceSource);
                b.setDiscountAmount(discount);
                b.setLateFee(money(null));
                b.setPaidAmount(money(null));
                b.setWaivedAmount(money(null));
                b.setPayableAmount(payable);
                b.setDueDate(dueDate);
                b.setBillDate(LocalDate.now());
                b.setBillStatus("UNPAID");
                b.setOverdueDays(0);
                b.setGenerateType("AUTO");
                b.setRuleId(effectiveRule == null ? null : effectiveRule.getId());
                b.setRuleVersion(effectiveRule == null ? null : effectiveRule.getRuleVersion());
                b.setRuleSnapshot(snapshot(effectiveRule));
                b.setBillingQuantity(qty);
                b.setBillingDays(pro.days());
                b.setProrationMonths(pro.months());
                b.setQuantityUnit(quantityUnit(mode));
                b.setQuantitySource(quantitySource(mode));
                b.setRemark("批量出账：" + item.getItemName()
                        + (effectiveRule == null ? "" : "（规则：" + effectiveRule.getRuleName() + "）")
                        + "；" + pro.detail()
                        + (discount.compareTo(BigDecimal.ZERO) > 0
                        ? "；补贴抵扣 " + discount.toPlainString() : ""));
                b.setIsDeleted(0);
                b.setCreateTime(now);
                billMapper.insert(b);
                billId = id;
            }
            generated++;
            total = total.add(amount);
            String explain = pro.detail().isEmpty()
                    ? calcExplain : calcExplain + "；" + pro.detail();
            if (effectiveRule != null) {
                explain = explain + "；规则：" + effectiveRule.getRuleName();
            }
            items.add(new GenerateResultVO.Item(ct.getId(), ct.getContractNo(), billId, qty,
                    amount, explain, "OK", null));
        }

        log.info("批量出账[{}]：合同 {}，生成 {}，跳过 {}，合计 {}",
                dryRun ? "试运行" : "已落库", contracts.size(), generated, skipped, total);

        return new GenerateResultVO(contracts.size(), generated, skipped, skipReasons,
                total.setScale(2, RoundingMode.HALF_UP), dryRun, items);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public GenerateBatchVO generateBatch(GenerateBatchCmd cmd) {
        // 批次级参数前置校验：期间、组织等属于整个批次共用的输入，
        // 无效时应当让整批直接失败（而不是逐项目返回 FAILED），便于调用方快速发现
        if (cmd.periodEnd().isBefore(cmd.periodStart())) {
            throw BizException.paramInvalid("费用截止日不能早于起始日");
        }
        boolean dryRun = cmd.dryRun() != null && cmd.dryRun();
        String batchNo = "GB" + System.currentTimeMillis();

        List<GenerateBatchVO.ItemResult> results = new ArrayList<>();
        int totalGenerated = 0;
        int totalSkipped = 0;
        BigDecimal totalAmount = BigDecimal.ZERO;

        for (GenerateBatchCmd.Item it : cmd.items()) {
            FinFeeItem item = feeItemMapper.selectById(it.feeItemId());
            String name = item == null ? String.valueOf(it.feeItemId()) : item.getItemName();
            try {
                // 单项目出账复用既有幂等逻辑
                GenerateResultVO one = generate(new GenerateBillsCmd(
                        it.feeItemId(), it.ruleId(), null,
                        cmd.periodStart(), cmd.periodEnd(),
                        cmd.billPeriod(), cmd.dueDate(),
                        cmd.orgId(), cmd.houseType(), cmd.contractIds(),
                        cmd.quantityOverride(), cmd.dryRun()));
                results.add(new GenerateBatchVO.ItemResult(it.feeItemId(), name, "OK", null, one));
                totalGenerated += one.generated();
                totalSkipped += one.skipped();
                totalAmount = totalAmount.add(one.totalAmount());
            } catch (Exception e) {
                // 项目间隔离：单项失败不影响其它项目
                log.warn("批量出账：项目 {}（{}）失败：{}", it.feeItemId(), name, e.getMessage());
                results.add(new GenerateBatchVO.ItemResult(it.feeItemId(), name, "FAILED",
                        e.getMessage(), null));
            }
        }

        log.info("多项目批量出账[{}] batchNo={} 项目 {} 生成 {} 跳过 {} 合计 {}",
                dryRun ? "试运行" : "已落库", batchNo, cmd.items().size(),
                totalGenerated, totalSkipped, totalAmount);

        return new GenerateBatchVO(batchNo, totalGenerated, totalSkipped,
                totalAmount.setScale(2, RoundingMode.HALF_UP), dryRun, results);
    }

    // race:ignore 管理员手工触发的历史账单重算：只改未缴且未收款（UNPAID、paid=0）的账单，
    // 并在单一事务内按 id 更新；并发收款会同时改账单状态/金额，冲突时会因条件不满足被跳过。
    @Override
    @Transactional(rollbackFor = Exception.class)
    public RecalcBillsResult recalculate(RecalcBillsCmd cmd) {
        // race:ignore 管理员手工触发的历史账单重算：只处理未缴且未收款账单，单事务内更新；
        // 并发收款会改变账单状态，重算结果以事务内读取为准，不涉及新增资金记录。
        boolean dryRun = cmd.dryRun() != null && cmd.dryRun();
        LambdaQueryWrapper<FinBill> qw = new LambdaQueryWrapper<FinBill>()
                .eq(FinBill::getIsDeleted, 0)
                .eq(FinBill::getBillStatus, "UNPAID")
                .eq(FinBill::getGenerateType, "AUTO")
                .and(w -> w.isNull(FinBill::getPaidAmount)
                        .or().eq(FinBill::getPaidAmount, BigDecimal.ZERO))
                .isNotNull(FinBill::getPeriodStart)
                .isNotNull(FinBill::getPeriodEnd)
                .eq(cmd.orgId() != null, FinBill::getOrgId, cmd.orgId())
                .eq(cmd.feeItemId() != null, FinBill::getFeeItemId, cmd.feeItemId())
                .ge(cmd.periodStart() != null, FinBill::getPeriodStart, cmd.periodStart())
                .le(cmd.periodEnd() != null, FinBill::getPeriodEnd, cmd.periodEnd())
                .orderByAsc(FinBill::getId)
                .last("limit 2000");
        java.util.List<FinBill> bills = billMapper.selectList(qw);

        java.util.List<RecalcBillsResult.Item> items = new java.util.ArrayList<>();
        int changed = 0;
        int skipped = 0;
        BigDecimal oldTotal = BigDecimal.ZERO;
        BigDecimal newTotal = BigDecimal.ZERO;
        java.time.LocalDateTime now = java.time.LocalDateTime.now();

        for (FinBill b : bills) {
            if (b.getFeeItemId() == null || b.getContractId() == null) {
                skipped++;
                items.add(new RecalcBillsResult.Item(b.getId(), b.getBillNo(), null,
                        b.getBillAmount(), null, null, null, "SKIPPED",
                        "账单缺少收费项目或合同，无法重算"));
                continue;
            }
            FinFeeItem item = feeItemMapper.selectById(b.getFeeItemId());
            if (item == null) {
                skipped++;
                continue;
            }
            CalcMode mode;
            try {
                mode = CalcMode.valueOf(item.getCalcMode());
            } catch (Exception e) {
                skipped++;
                continue;
            }
            if (mode == CalcMode.METER || mode == CalcMode.BY_NIGHT) {
                skipped++;
                items.add(new RecalcBillsResult.Item(b.getId(), b.getBillNo(), null,
                        b.getBillAmount(), null, null, null, "SKIPPED",
                        "按抄表/按夜计费不按月折算，跳过"));
                continue;
            }
            BizContract ct = contractMapper.selectById(b.getContractId());
            if (ct == null || ct.getLeaseStart() == null || ct.getLeaseEnd() == null) {
                skipped++;
                items.add(new RecalcBillsResult.Item(b.getId(), b.getBillNo(), null,
                        b.getBillAmount(), null, null, null, "SKIPPED", "合同或租期缺失，无法折算"));
                continue;
            }
            AssetHouse house = b.getHouseId() == null ? null
                    : houseMapper.selectById(b.getHouseId());
            if (mode.needsArea() && (house == null || house.getArea() == null
                    || house.getArea().compareTo(BigDecimal.ZERO) <= 0)) {
                skipped++;
                items.add(new RecalcBillsResult.Item(b.getId(), b.getBillNo(), ct.getContractNo(),
                        b.getBillAmount(), null, null, null, "SKIPPED", "房源未录面积"));
                continue;
            }
            Proration pro = proration(ct, b.getPeriodStart(), b.getPeriodEnd());
            if (pro.months().compareTo(BigDecimal.ZERO) <= 0) {
                skipped++;
                items.add(new RecalcBillsResult.Item(b.getId(), b.getBillNo(), ct.getContractNo(),
                        b.getBillAmount(), null, 0, null, "SKIPPED", "租期与费用区间无交集"));
                continue;
            }
            Integer qty = quantityOf(mode, ct, house, 0, null);
            BigDecimal price = item.getUnitPrice() == null ? BigDecimal.ZERO : item.getUnitPrice();
            BigDecimal base = switch (mode) {
                case FIXED, BY_HOUSE -> price;
                case BY_AREA -> price.multiply(house.getArea());
                case BY_PERSON, BY_BED -> price.multiply(BigDecimal.valueOf(qty));
                default -> price;
            };
            BigDecimal newAmount = base.multiply(pro.months())
                    .setScale(2, RoundingMode.HALF_UP);
            BigDecimal oldAmount = b.getBillAmount() == null
                    ? BigDecimal.ZERO : b.getBillAmount();
            if (newAmount.compareTo(oldAmount) == 0) {
                items.add(new RecalcBillsResult.Item(b.getId(), b.getBillNo(), ct.getContractNo(),
                        oldAmount, newAmount, pro.days(), pro.detail(), "SAME", null));
                continue;
            }
            oldTotal = oldTotal.add(oldAmount);
            newTotal = newTotal.add(newAmount);
            changed++;
            if (!dryRun) {
                b.setBillAmount(newAmount);
                BigDecimal waived = b.getWaivedAmount() == null
                        ? BigDecimal.ZERO : b.getWaivedAmount();
                BigDecimal payable = newAmount.subtract(waived)
                        .setScale(2, RoundingMode.HALF_UP);
                b.setPayableAmount(payable.max(BigDecimal.ZERO));
                b.setRemark((b.getRemark() == null ? "" : b.getRemark() + "；")
                        + "按新规则重算：" + oldAmount + " → " + newAmount
                        + "（" + pro.detail() + "）");
                b.setUpdateTime(now);
                billMapper.updateById(b);
            }
            items.add(new RecalcBillsResult.Item(b.getId(), b.getBillNo(), ct.getContractNo(),
                    oldAmount, newAmount, pro.days(), pro.detail(),
                    "CHANGED", dryRun ? "试算未落库" : null));
        }

        log.info("历史账单重算[{}]：扫描 {}，变更 {}，跳过 {}，{} → {}",
                dryRun ? "试运行" : "已落库", bills.size(), changed, skipped, oldTotal, newTotal);
        return new RecalcBillsResult(bills.size(), changed, skipped,
                oldTotal.setScale(2, RoundingMode.HALF_UP),
                newTotal.setScale(2, RoundingMode.HALF_UP), dryRun, items);
    }

    @Override
    public BillExplainVO explain(Long billId) {
        FinBill b = billMapper.selectById(billId);
        if (b == null) {
            throw BizException.notFound("账单");
        }
        FinFeeItem item = b.getFeeItemId() == null ? null
                : feeItemMapper.selectById(b.getFeeItemId());
        CalcMode mode = null;
        String modeLabel = "";
        if (item != null) {
            try {
                mode = CalcMode.valueOf(item.getCalcMode());
                modeLabel = mode.label();
            } catch (Exception ignore) {
            }
        }
        BizContract ct = b.getContractId() == null ? null
                : contractMapper.selectById(b.getContractId());
        AssetHouse house = b.getHouseId() == null ? null
                : houseMapper.selectById(b.getHouseId());

        BigDecimal price = item == null || item.getUnitPrice() == null
                ? BigDecimal.ZERO : item.getUnitPrice();
        BigDecimal area = house == null ? null : house.getArea();
        Integer qty = null;
        Integer days = null;
        BigDecimal months = BigDecimal.ONE;
        String formula = "—";
        if (mode != null && ct != null && ct.getLeaseStart() != null
                && b.getPeriodStart() != null && b.getPeriodEnd() != null) {
            Proration pro = proration(ct, b.getPeriodStart(), b.getPeriodEnd());
            days = pro.days();
            months = pro.months();
        }
        if (mode == CalcMode.BY_NIGHT) {
            nightsOf(b, ct);
            days = (int) Math.max(1, ChronoUnit.DAYS.between(b.getPeriodStart(), b.getPeriodEnd()));
            qty = days;
            months = BigDecimal.ONE;
            formula = "天数 × 单价";
        } else if (mode == CalcMode.METER) {
            formula = "用量 × 单价（用量见抄表记录）";
            months = BigDecimal.ONE;
        } else if (mode == CalcMode.BY_AREA) {
            qty = 1;
            formula = "面积 × 单价 × 月数";
        } else if (mode == CalcMode.BY_PERSON || mode == CalcMode.BY_BED) {
            qty = quantityOf(mode, ct, house, 0, null);
            formula = "数量 × 单价 × 月数";
        } else if (mode != null) {
            qty = 1;
            formula = "单价 × 月数";
        }

        BigDecimal amount = b.getBillAmount();
        // 短租/订单类账单单价来自订单，项目单价可能为 0：按账单金额反推展示
        if (price.compareTo(BigDecimal.ZERO) == 0 && amount != null
                && amount.compareTo(BigDecimal.ZERO) > 0 && qty != null && qty > 0) {
            price = amount.divide(BigDecimal.valueOf(qty), 4, RoundingMode.HALF_UP);
        }
        java.util.List<BillExplainVO.Line> lines = new java.util.ArrayList<>();
        lines.add(new BillExplainVO.Line("收费项目", item == null ? "—" : item.getItemName()));
        lines.add(new BillExplainVO.Line("计费方式", modeLabel));
        String unit = item == null ? null : item.getUnit();
        String priceText = price.toPlainString()
                + (unit == null || unit.isBlank() ? ""
                : (unit.contains("元") ? " " + unit : " 元/" + unit));
        lines.add(new BillExplainVO.Line("单价", priceText));
        if (mode == CalcMode.BY_AREA) {
            lines.add(new BillExplainVO.Line("建筑面积", area == null ? "—" : area.toPlainString() + " ㎡"));
        }
        if (qty != null && mode != CalcMode.BY_AREA) {
            lines.add(new BillExplainVO.Line("数量", String.valueOf(qty)));
        }
        if (b.getPeriodStart() != null && b.getPeriodEnd() != null) {
            lines.add(new BillExplainVO.Line("费用区间",
                    b.getPeriodStart() + " ~ " + b.getPeriodEnd()));
        }
        if (days != null) {
            lines.add(new BillExplainVO.Line("计费天数", days + " 天"));
        }
        if (mode != CalcMode.METER && mode != CalcMode.BY_NIGHT) {
            lines.add(new BillExplainVO.Line("折算月数", months.stripTrailingZeros().toPlainString()));
        }
        lines.add(new BillExplainVO.Line("计算公式", formula));
        lines.add(new BillExplainVO.Line("应收金额", amount == null ? "0.00" : amount.toPlainString()));
        if (b.getRemark() != null && !b.getRemark().isBlank()) {
            lines.add(new BillExplainVO.Line("计费说明", b.getRemark()));
        }
        return new BillExplainVO(b.getId(), b.getBillNo(),
                item == null ? null : item.getItemName(),
                mode == null ? null : mode.name(), modeLabel, price, area, qty, days, months,
                formula, amount, b.getRemark(), lines);
    }

    /** 按夜计费天数（保留占位，避免空指针）。 */
    private static int nightsOf(FinBill b, BizContract ct) {
        return 0;
    }

    /** 数量取值：按合同实际保障人口/实际床位，不再取房源 maxCapacity。 */
private Integer quantityOf(CalcMode mode, BizContract ct, AssetHouse house, int nights,
                           Integer override) {
    if (override != null && override > 0) {
        return override;
    }
    return switch (mode) {
        case BY_NIGHT -> nights;
        case BY_PERSON -> personCount(ct);
        case BY_BED -> bedCount(ct);
        case FIXED, BY_HOUSE, BY_AREA -> 1;
        case METER -> 1;
    };
}

/** 保障人口 = 承租人 1 + 同住人。 */
private int personCount(BizContract ct) {
    if (ct == null || ct.getId() == null) {
        return 1;
    }
    Long n = cohabitantMapper.selectCount(new LambdaQueryWrapper<BizContractCohabitant>()
            .eq(BizContractCohabitant::getContractId, ct.getId()));
    return 1 + (n == null ? 0 : n.intValue());
}

/** 实际签约床位数，默认 1。 */
private static int bedCount(BizContract ct) {
    return ct != null && ct.getBillingBedCount() != null && ct.getBillingBedCount() > 0
            ? ct.getBillingBedCount() : 1;
}

private static String quantityUnit(CalcMode mode) {
    return switch (mode) {
        case BY_PERSON -> "PERSON";
        case BY_BED -> "BED";
        case BY_NIGHT -> "NIGHT";
        case BY_AREA -> "AREA";
        default -> "HOUSE";
    };
}

private static String quantitySource(CalcMode mode) {
    return switch (mode) {
        case BY_PERSON -> "COHABITANT";
        case BY_BED -> "CONTRACT";
        default -> "DEFAULT";
    };
}

/** 自动匹配规则：组织/房源类型/保障类型/生效期/优先级。 */
private static FinBillingRule matchRule(List<FinBillingRule> rules, BizContract ct,
                                        AssetHouse house, LocalDate ps, LocalDate pe) {
    if (rules == null || rules.isEmpty()) {
        return null;
    }
    String houseType = house == null ? null : house.getHouseType();
    String security = securityTypeOf(ct.getContractType());
    FinBillingRule best = null;
    int bestScore = Integer.MIN_VALUE;
    for (FinBillingRule r : rules) {
        if (r.getOrgId() != null && !r.getOrgId().equals(ct.getOrgId())) {
            continue;
        }
        if (r.getHouseType() != null && !r.getHouseType().isBlank()
                && !r.getHouseType().equals(houseType)) {
            continue;
        }
        if (r.getSecurityType() != null && !r.getSecurityType().isBlank()
                && !r.getSecurityType().equals(security)) {
            continue;
        }
        // 合同暂无收入档数据：规则限定收入档时不参与自动匹配，避免误用
        if (r.getIncomeLevel() != null && !r.getIncomeLevel().isBlank()) {
            continue;
        }
        if (r.getEffectiveStart() != null && r.getEffectiveStart().isAfter(ps)) {
            continue;
        }
        if (r.getEffectiveEnd() != null && r.getEffectiveEnd().isBefore(pe)) {
            continue;
        }
        int score = (r.getOrgId() == null ? 0 : 100)
                + (r.getSecurityType() == null || r.getSecurityType().isBlank() ? 0 : 20)
                + (r.getHouseType() == null || r.getHouseType().isBlank() ? 0 : 10)
                + (r.getPriority() == null ? 0 : r.getPriority());
        if (score > bestScore
                || (score == bestScore && best != null
                    && r.getId() != null && best.getId() != null
                    && r.getId() > best.getId())) {
            best = r;
            bestScore = score;
        }
    }
    return best;
}

private static String securityTypeOf(String contractType) {
    if (contractType == null) {
        return "PUBLIC";
    }
    if (contractType.contains("PUBLIC")) {
        return "PUBLIC";
    }
    if (contractType.contains("LOW")) {
        return "LOW";
    }
    return contractType;
}

/** 规则快照：规则后续修改不影响历史账单解释。 */
private static String snapshot(FinBillingRule r) {
    if (r == null) {
        return null;
    }
    try {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", r.getId());
        m.put("code", r.getRuleCode());
        m.put("name", r.getRuleName());
        m.put("version", r.getRuleVersion());
        m.put("type", r.getRuleType());
        m.put("config", r.getPriceConfig());
        m.put("priority", r.getPriority());
        return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(m);
    } catch (Exception e) {
        return "{}";
    }
}

/** 账期统一为 yyyy-MM（兼容前端传入 yyyyMM）。 */
private static String normalizePeriod(String period, LocalDate start) {
    if (period == null || period.isBlank()) {
        return start.format(PERIOD_FMT);
    }
    String p = period.trim().replace("/", "-");
    if (p.matches("\\d{6}")) {
        return p.substring(0, 4) + "-" + p.substring(4);
    }
    if (p.matches("\\d{4}-\\d{2}")) {
        return p;
    }
    return start.format(PERIOD_FMT);
}

/** 构造计算上下文。 */
    private static BillingCalculator.Context contextOf(CalcMode mode, AssetHouse house,
                                                       int nights, Integer qty) {
        return switch (mode) {
            case BY_AREA -> BillingCalculator.Context.ofArea(house.getArea());
            case BY_PERSON, BY_BED, BY_NIGHT -> BillingCalculator.Context.ofQuantity(qty);
            default -> BillingCalculator.Context.empty();
        };
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }

    /** 计费折算结果：月数、计费天数、可读说明。 */
    private record Proration(BigDecimal months, int days, String detail) {
    }

    /**
     * 按「费用区间 ∩ 合同租期」逐月折算月数。
     *
     * <p>规则：整自然月 = 1 个月；不足整月或跨月，按每月实际天数占比累加，
     * 例如 9/10–10/10 = 21/30（9 月）+ 10/31（10 月）。
     */
    private static Proration proration(BizContract ct, LocalDate ps, LocalDate pe) {
        LocalDate start = ct.getLeaseStart() != null && ct.getLeaseStart().isAfter(ps)
                ? ct.getLeaseStart() : ps;
        LocalDate end = ct.getLeaseEnd() != null && ct.getLeaseEnd().isBefore(pe)
                ? ct.getLeaseEnd() : pe;
        if (start.isAfter(end)) {
            return new Proration(BigDecimal.ZERO, 0, "合同租期与费用区间无交集");
        }
        int totalDays = (int) ChronoUnit.DAYS.between(start, end) + 1;
        BigDecimal months = BigDecimal.ZERO;
        StringBuilder detail = new StringBuilder();
        LocalDate cursor = start;
        while (!cursor.isAfter(end)) {
            LocalDate monthEnd = cursor.withDayOfMonth(cursor.lengthOfMonth());
            LocalDate segEnd = monthEnd.isAfter(end) ? end : monthEnd;
            int segDays = (int) ChronoUnit.DAYS.between(cursor, segEnd) + 1;
            BigDecimal frac = BigDecimal.valueOf(segDays)
                    .divide(BigDecimal.valueOf(cursor.lengthOfMonth()), 6, RoundingMode.HALF_UP);
            months = months.add(frac);
            if (detail.length() > 0) {
                detail.append(" + ");
            }
            detail.append(cursor.getMonthValue()).append("月")
                    .append(segDays).append("/").append(cursor.lengthOfMonth());
            cursor = segEnd.plusDays(1);
        }
        months = months.setScale(6, RoundingMode.HALF_UP);
        String text = "计费 " + totalDays + " 天（" + detail + "）";
        return new Proration(months, totalDays, text);
    }
}
