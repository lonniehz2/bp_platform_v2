package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.dto.BillingRuleCreateCmd;
import com.yundao.bp.fin.dto.CalcPreviewCmd;
import com.yundao.bp.fin.dto.FeeItemCreateCmd;
import com.yundao.bp.fin.dto.FeeItemVO;
import com.yundao.bp.fin.entity.FinBillingRule;
import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.mapper.FinBillingRuleMapper;
import com.yundao.bp.fin.mapper.FinFeeItemMapper;
import com.yundao.bp.fin.service.BillingCalculator;
import com.yundao.bp.fin.service.FeeItemService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 收费项目与计费规则实现。
 */
@Service
public class FeeItemServiceImpl implements FeeItemService {

    private static final Logger log = LoggerFactory.getLogger(FeeItemServiceImpl.class);

    private final FinFeeItemMapper feeItemMapper;
    private final FinBillingRuleMapper ruleMapper;
    private final BillingCalculator calculator;
    private final SnowflakeIdGenerator idGen;

    public FeeItemServiceImpl(FinFeeItemMapper feeItemMapper, FinBillingRuleMapper ruleMapper,
                              BillingCalculator calculator, SnowflakeIdGenerator idGen) {
        this.feeItemMapper = feeItemMapper;
        this.ruleMapper = ruleMapper;
        this.calculator = calculator;
        this.idGen = idGen;
    }

    // ==================== 收费项目 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FeeItemVO createFeeItem(FeeItemCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        Long dup = feeItemMapper.selectCount(new LambdaQueryWrapper<FinFeeItem>()
                .eq(FinFeeItem::getItemCode, cmd.itemCode()));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "收费项目编码已存在: " + cmd.itemCode());
        }
        long id = idGen.nextId();
        FinFeeItem e = new FinFeeItem();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setItemCode(cmd.itemCode());
        e.setItemName(cmd.itemName());
        e.setItemType(cmd.itemType());
        e.setSecurityType(cmd.securityType());
        e.setCalcMode(cmd.calcMode());
        e.setUnitPrice(cmd.unitPrice());
        e.setUnit(cmd.unit());
        e.setStatus("ENABLED");
        e.setIsDeleted(0);
        e.setCreateTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        feeItemMapper.insert(e);
        return FeeItemVO.from(e);
    }

    @Override
    public FeeItemVO getFeeItem(Long id) {
        FinFeeItem e = feeItemMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("收费项目");
        }
        return FeeItemVO.from(e);
    }

    @Override
    public PageResult<FeeItemVO> pageFeeItems(long pageNum, long pageSize, String itemType,
                                              String calcMode, String keyword) {
        // scope:ignore 计费项为租户级配置
        LambdaQueryWrapper<FinFeeItem> qw = new LambdaQueryWrapper<FinFeeItem>()
                .eq(itemType != null && !itemType.isBlank(), FinFeeItem::getItemType, itemType)
                .eq(calcMode != null && !calcMode.isBlank(), FinFeeItem::getCalcMode, calcMode)
                .orderByDesc(FinFeeItem::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(FinFeeItem::getItemName, keyword)
                    .or().like(FinFeeItem::getItemCode, keyword));
        }
        IPage<FinFeeItem> page = feeItemMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<FeeItemVO> rows = page.getRecords().stream().map(FeeItemVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FeeItemVO setFeeItemStatus(Long id, boolean enabled) {
        FinFeeItem e = feeItemMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("收费项目");
        }
        e.setStatus(enabled ? "ENABLED" : "DISABLED");
        e.setUpdateTime(LocalDateTime.now());
        feeItemMapper.updateById(e);
        return FeeItemVO.from(e);
    }

    // ==================== 计费规则 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FinBillingRule createRule(BillingRuleCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        FinFeeItem item = feeItemMapper.selectById(cmd.feeItemId());
        if (item == null) {
            throw BizException.notFound("收费项目");
        }
        if (cmd.effectiveStart() != null && cmd.effectiveEnd() != null
                && !cmd.effectiveEnd().isAfter(cmd.effectiveStart())) {
            throw BizException.paramInvalid("生效结束日必须晚于开始日");
        }
        long id = idGen.nextId();
        FinBillingRule e = new FinBillingRule();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setRuleCode(cmd.ruleCode());
        e.setRuleName(cmd.ruleName());
        e.setFeeItemId(cmd.feeItemId());
        e.setOrgId(cmd.orgId());
        e.setHouseType(cmd.houseType());
        e.setSecurityType(cmd.securityType());
        e.setIncomeLevel(cmd.incomeLevel());
        e.setRuleType(cmd.ruleType());
        e.setPriceConfig(cmd.priceConfig());
        e.setEffectiveStart(cmd.effectiveStart() == null ? LocalDate.now() : cmd.effectiveStart());
        e.setEffectiveEnd(cmd.effectiveEnd());
        e.setPriority(cmd.priority() == null ? 0 : cmd.priority());
        e.setRuleVersion(1);
        // 租金类规则需政府限价审批，其它类型直接通过
        e.setApproveStatus("RENT".equals(item.getItemType()) ? "PENDING" : "APPROVED");
        e.setStatus("ENABLED");
        e.setIsDeleted(0);
        e.setCreateTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        ruleMapper.insert(e);
        if ("PENDING".equals(e.getApproveStatus())) {
            log.info("租金规则 {} 待政府限价审批", e.getRuleCode());
        }
        return e;
    }

    @Override
    public FinBillingRule getRule(Long id) {
        FinBillingRule e = ruleMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("计费规则");
        }
        return e;
    }

    @Override
    public List<FinBillingRule> listRules(Long feeItemId, String houseType) {
        return ruleMapper.selectList(new LambdaQueryWrapper<FinBillingRule>()
                .eq(feeItemId != null, FinBillingRule::getFeeItemId, feeItemId)
                .eq(houseType != null && !houseType.isBlank(),
                        FinBillingRule::getHouseType, houseType)
                .eq(FinBillingRule::getStatus, "ENABLED")
                .orderByDesc(FinBillingRule::getPriority)
                .orderByDesc(FinBillingRule::getId));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FinBillingRule approveRule(Long id, Long approveById) {
        FinBillingRule e = ruleMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("计费规则");
        }
        if ("APPROVED".equals(e.getApproveStatus())) {
            throw BizException.stateConflict("规则已审批通过");
        }
        e.setApproveStatus("APPROVED");
        e.setApproveById(approveById);
        e.setApproveTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        ruleMapper.updateById(e);
        return e;
    }

    // ==================== 试算 ====================

    @Override
    public BillingCalculator.Result preview(CalcPreviewCmd cmd) {
        FinFeeItem item = feeItemMapper.selectById(cmd.feeItemId());
        if (item == null) {
            throw BizException.notFound("收费项目");
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
        BillingCalculator.Context ctx = new BillingCalculator.Context(
                cmd.area(), cmd.quantity(), cmd.meterStart(), cmd.meterEnd());
        return calculator.calculate(item, ctx, rule);
    }
}
