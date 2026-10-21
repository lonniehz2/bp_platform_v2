# -*- coding: utf-8 -*-
"""生成 fin 计费引擎（服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/dto/FeeItemCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

/**
 * 创建收费项目。
 *
 * <p>⭐ {@code calcMode} 决定该费用"按什么算"，是<b>多业态适配的核心开关</b>：
 * <ul>
 *   <li>保障房租金 → {@code BY_AREA} / {@code BY_HOUSE}</li>
 *   <li>宿舍床位费 → {@code BY_BED}</li>
 *   <li>酒店/民宿/网约房 → {@code BY_NIGHT}</li>
 *   <li>园区水电能耗费 → {@code METER}</li>
 * </ul>
 */
public record FeeItemCreateCmd(

        @NotBlank(message = "项目编码不能为空")
        @Size(max = 64, message = "编码不能超过 64 字符")
        String itemCode,

        @NotBlank(message = "项目名称不能为空")
        @Size(max = 128, message = "名称不能超过 128 字符")
        String itemName,

        @NotBlank(message = "项目类型不能为空")
        @Pattern(regexp = "RENT|PROPERTY|PARKING|ENERGY|DEPOSIT|LATE_FEE|OTHER",
                message = "项目类型不合法")
        String itemType,

        String securityType,

        @NotBlank(message = "计费方式不能为空")
        @Pattern(regexp = "FIXED|BY_AREA|BY_HOUSE|BY_PERSON|BY_BED|BY_NIGHT|METER",
                message = "计费方式不合法")
        String calcMode,

        @DecimalMin(value = "0", message = "单价不能为负")
        BigDecimal unitPrice,

        String unit
) {
}
'''

FILES['fin/dto/BillingRuleCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

/**
 * 创建计费规则。
 *
 * <p>{@code priceConfig} 按规则类型填：
 * <pre>
 *   STANDARD : {"price": 12.50}
 *   TIERED   : {"tiers":[{"limit":50,"price":3.0},{"limit":null,"price":5.0}]}
 *   DISCOUNT : {"rate": 0.9}
 *   EXEMPT   : {}
 * </pre>
 */
public record BillingRuleCreateCmd(

        @NotBlank(message = "规则编码不能为空")
        @Size(max = 64, message = "编码不能超过 64 字符")
        String ruleCode,

        @NotBlank(message = "规则名称不能为空")
        @Size(max = 128, message = "名称不能超过 128 字符")
        String ruleName,

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        Long orgId,
        /** 适用房源类型（多业态：PUBLIC_RENTAL / DORMITORY / HOTEL ...） */
        String houseType,
        String securityType,
        String incomeLevel,

        @NotBlank(message = "规则类型不能为空")
        @Pattern(regexp = "STANDARD|TIERED|DISCOUNT|EXEMPT", message = "规则类型不合法")
        String ruleType,

        @NotBlank(message = "价格配置不能为空")
        String priceConfig,

        LocalDate effectiveStart,
        LocalDate effectiveEnd,
        Integer priority
) {
}
'''

FILES['fin/dto/FeeItemVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.CalcMode;
import com.yundao.bp.fin.entity.FinFeeItem;
import java.math.BigDecimal;

/**
 * 收费项目视图。
 */
public record FeeItemVO(
        Long id,
        String itemCode,
        String itemName,
        String itemType,
        String securityType,
        String calcMode,
        String calcModeLabel,
        BigDecimal unitPrice,
        String unit,
        String status
) {
    public static FeeItemVO from(FinFeeItem e) {
        if (e == null) {
            return null;
        }
        CalcMode m;
        try {
            m = CalcMode.valueOf(e.getCalcMode());
        } catch (IllegalArgumentException ex) {
            m = CalcMode.FIXED;
        }
        return new FeeItemVO(e.getId(), e.getItemCode(), e.getItemName(), e.getItemType(),
                e.getSecurityType(), e.getCalcMode(), m.label(), e.getUnitPrice(), e.getUnit(),
                e.getStatus());
    }
}
'''

FILES['fin/dto/CalcPreviewCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * 试算请求（不落库，用于验证计费规则是否正确）。
 */
public record CalcPreviewCmd(

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        /** 可选：指定规则；不传则用项目默认单价 */
        Long ruleId,

        BigDecimal area,
        Integer quantity,
        BigDecimal meterStart,
        BigDecimal meterEnd
) {
}
'''

FILES['fin/service/FeeItemService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.BillingRuleCreateCmd;
import com.yundao.bp.fin.dto.CalcPreviewCmd;
import com.yundao.bp.fin.dto.FeeItemCreateCmd;
import com.yundao.bp.fin.dto.FeeItemVO;
import com.yundao.bp.fin.entity.FinBillingRule;
import java.util.List;

/**
 * 收费项目与计费规则服务。
 */
public interface FeeItemService {

    FeeItemVO createFeeItem(FeeItemCreateCmd cmd);

    FeeItemVO getFeeItem(Long id);

    PageResult<FeeItemVO> pageFeeItems(long pageNum, long pageSize, String itemType,
                                       String calcMode, String keyword);

    /** 启用/停用收费项目。 */
    FeeItemVO setFeeItemStatus(Long id, boolean enabled);

    FinBillingRule createRule(BillingRuleCreateCmd cmd);

    FinBillingRule getRule(Long id);

    List<FinBillingRule> listRules(Long feeItemId, String houseType);

    /** 政府限价审批通过（租金定价管控）。 */
    FinBillingRule approveRule(Long id, Long approveById);

    /** 试算：给定收费项目 + 上下文（可指定规则），返回金额与计算过程。 */
    BillingCalculator.Result preview(CalcPreviewCmd cmd);
}
'''

FILES['fin/service/impl/FeeItemServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

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
'''

FILES['fin/controller/FeeItemController.java'] = '''package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.BillingRuleCreateCmd;
import com.yundao.bp.fin.dto.CalcPreviewCmd;
import com.yundao.bp.fin.dto.FeeItemCreateCmd;
import com.yundao.bp.fin.dto.FeeItemVO;
import com.yundao.bp.fin.entity.FinBillingRule;
import com.yundao.bp.fin.service.BillingCalculator;
import com.yundao.bp.fin.service.FeeItemService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 收费项目与计费规则接口（BC-08）。
 *
 * <p>⭐ <b>多业态适配点</b>：通过 {@code calcMode}（按面积/按套/按床位/按夜/按抄表）
 * + {@code ruleType}（标准价/阶梯/折扣/减免）的组合，覆盖保障房、宿舍、公寓、
 * 酒店民宿、园区物业等不同业态的计费差异，无需改代码。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class FeeItemController {

    private final FeeItemService service;

    public FeeItemController(FeeItemService service) {
        this.service = service;
    }

    @PostMapping("/fee-items")
    public R<FeeItemVO> createFeeItem(@Valid @RequestBody FeeItemCreateCmd cmd) {
        return R.ok(service.createFeeItem(cmd));
    }

    @GetMapping("/fee-items/{id}")
    public R<FeeItemVO> getFeeItem(@PathVariable Long id) {
        return R.ok(service.getFeeItem(id));
    }

    @GetMapping("/fee-items")
    public R<PageResult<FeeItemVO>> pageFeeItems(@RequestParam(defaultValue = "1") long pageNum,
                                                 @RequestParam(defaultValue = "20") long pageSize,
                                                 @RequestParam(required = false) String itemType,
                                                 @RequestParam(required = false) String calcMode,
                                                 @RequestParam(required = false) String keyword) {
        return R.ok(service.pageFeeItems(pageNum, pageSize, itemType, calcMode, keyword));
    }

    @PostMapping("/fee-items/{id}/status")
    public R<FeeItemVO> setStatus(@PathVariable Long id,
                                  @RequestBody(required = false) StatusCmd cmd) {
        return R.ok(service.setFeeItemStatus(id, cmd != null && cmd.enabled()));
    }

    @PostMapping("/billing-rules")
    public R<FinBillingRule> createRule(@Valid @RequestBody BillingRuleCreateCmd cmd) {
        return R.ok(service.createRule(cmd));
    }

    @GetMapping("/billing-rules/{id}")
    public R<FinBillingRule> getRule(@PathVariable Long id) {
        return R.ok(service.getRule(id));
    }

    @GetMapping("/billing-rules")
    public R<List<FinBillingRule>> listRules(@RequestParam(required = false) Long feeItemId,
                                             @RequestParam(required = false) String houseType) {
        return R.ok(service.listRules(feeItemId, houseType));
    }

    /** 政府限价审批。 */
    @PostMapping("/billing-rules/{id}/approve")
    public R<FinBillingRule> approveRule(@PathVariable Long id,
                                         @RequestBody(required = false) ApproveCmd cmd) {
        return R.ok(service.approveRule(id, cmd == null ? null : cmd.approveById()));
    }

    /** 试算（不落库）。 */
    @PostMapping("/calc-preview")
    public R<BillingCalculator.Result> preview(@Valid @RequestBody CalcPreviewCmd cmd) {
        return R.ok(service.preview(cmd));
    }

    public record StatusCmd(boolean enabled) {
    }

    public record ApproveCmd(Long approveById) {
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
