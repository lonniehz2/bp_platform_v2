# -*- coding: utf-8 -*-
"""生成 fin 计费引擎（收费项目 + 计费规则 + 算费 + 批量出账）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ==================== 常量 ====================
FILES['fin/constant/CalcMode.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 计费方式（对应 {@code bp_fin_fee_item.calc_mode}）。
 *
 * <p>⭐ <b>多业态支持的关键</b>：不同业态用不同计费方式——
 * <ul>
 *   <li>保障房/长租公寓：{@link #BY_AREA} 按面积、{@link #BY_HOUSE} 按套、{@link #BY_BED} 按床位</li>
 *   <li>宿舍：{@link #BY_BED} 按床位</li>
 *   <li>酒店/民宿/网约房：{@link #BY_NIGHT} 按夜</li>
 *   <li>园区/物业能耗费：{@link #METER} 按抄表</li>
 * </ul>
 */
public enum CalcMode {

    FIXED("固定额"),
    BY_AREA("按面积"),
    BY_HOUSE("按套"),
    BY_PERSON("按人"),
    BY_BED("按床位"),
    BY_NIGHT("按夜"),
    METER("按抄表");

    private final String label;

    CalcMode(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要面积参与计算。 */
    public boolean needsArea() {
        return this == BY_AREA;
    }

    /** 是否需要数量（人数/床数/天数）参与计算。 */
    public boolean needsQuantity() {
        return this == BY_PERSON || this == BY_BED || this == BY_NIGHT;
    }

    /** 是否需要抄表读数（本次读数 - 上次读数）。 */
    public boolean needsMeter() {
        return this == METER;
    }
}
'''

FILES['fin/constant/RuleType.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 计费规则类型（对应 {@code bp_fin_billing_rule.rule_type}）。
 *
 * <p>多条规则命中时按 {@code priority} 取高者。
 */
public enum RuleType {

    STANDARD("标准价"),
    TIERED("阶梯"),
    DISCOUNT("折扣"),
    EXEMPT("减免");

    private final String label;

    RuleType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

# ==================== 实体 ====================
FILES['fin/entity/FinFeeItem.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 收费项目。对应 {@code bp_fin_fee_item}。
 */
@Data
@TableName("bp_fin_fee_item")
public class FinFeeItem {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String itemCode;
    private String itemName;

    /** RENT / PROPERTY / PARKING / ENERGY / DEPOSIT / LATE_FEE / OTHER */
    private String itemType;
    /** 适用保障类型（NULL 通用） */
    private String securityType;
    /** FIXED / BY_AREA / BY_HOUSE / BY_PERSON / BY_BED / BY_NIGHT / METER */
    private String calcMode;
    private BigDecimal unitPrice;
    private String unit;

    /** ENABLED / DISABLED */
    private String status;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['fin/entity/FinBillingRule.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 计费规则。对应 {@code bp_fin_billing_rule}。
 *
 * <p>{@code price_config} 为 JSON，按 {@link com.yundao.bp.fin.constant.RuleType} 解释：
 * <pre>
 *   STANDARD : {"price": 12.50}
 *   TIERED   : {"tiers":[{"limit":50,"price":3.0},{"limit":null,"price":5.0}]}
 *   DISCOUNT : {"rate": 0.9}            // 9 折
 *   EXEMPT   : {}                        // 全额减免
 * </pre>
 */
@Data
@TableName("bp_fin_billing_rule")
public class FinBillingRule {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String ruleCode;
    private String ruleName;
    private Long feeItemId;

    /** 适用组织（NULL 全租户） */
    private Long orgId;
    /** 适用房源类型（多业态适配点） */
    private String houseType;
    private String securityType;
    private String incomeLevel;

    /** STANDARD / TIERED / DISCOUNT / EXEMPT */
    private String ruleType;
    /** 价格配置 JSON */
    private String priceConfig;

    private LocalDate effectiveStart;
    private LocalDate effectiveEnd;
    private Integer priority;
    private Integer ruleVersion;

    /** PENDING / APPROVED / REJECTED（政府限价审批） */
    private String approveStatus;
    private Long approveById;
    private LocalDateTime approveTime;

    /** ENABLED / DISABLED */
    private String status;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

for mapper, entity in (('FinFeeItemMapper', 'FinFeeItem'),
                       ('FinBillingRuleMapper', 'FinBillingRule')):
    FILES['fin/mapper/%s.java' % mapper] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

# ==================== 计费引擎（纯计算，易测）====================
FILES['fin/service/BillingCalculator.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.fin.constant.CalcMode;
import com.yundao.bp.fin.constant.RuleType;
import com.yundao.bp.fin.entity.FinBillingRule;
import com.yundao.bp.fin.entity.FinFeeItem;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * 计费计算器（纯函数式，无数据库依赖，便于单测与复用）。
 *
 * <p><b>计算流程</b>：
 * <pre>
 *   基础金额 = f(计费方式, 单价, 面积/数量/读数)   ← CalcMode
 *   再按规则调整 = g(规则类型, 价格配置)           ← RuleType
 *   最终金额 = round(调整后, 2)
 * </pre>
 *
 * <p><b>多业态适配</b>：计费方式决定"按什么算"，
 * 规则决定"什么价"；两者组合即可覆盖
 * 保障房（按面积/按套）、宿舍（按床位）、酒店民宿（按夜）、园区（按抄表）。
 */
@Service
public class BillingCalculator {

    private static final Logger log = LoggerFactory.getLogger(BillingCalculator.class);

    /**
     * 计费上下文。
     *
     * @param area       面积（㎡），BY_AREA 必填
     * @param quantity   数量（人数/床数/天数），BY_PERSON/BY_BED/BY_NIGHT 必填
     * @param meterStart 上次读数，METER 必填
     * @param meterEnd   本次读数，METER 必填
     */
    public record Context(BigDecimal area, Integer quantity,
                          BigDecimal meterStart, BigDecimal meterEnd) {

        public static Context ofArea(BigDecimal area) {
            return new Context(area, null, null, null);
        }

        public static Context ofQuantity(int quantity) {
            return new Context(null, quantity, null, null);
        }

        public static Context ofMeter(BigDecimal start, BigDecimal end) {
            return new Context(null, null, start, end);
        }

        public static Context empty() {
            return new Context(null, null, null, null);
        }
    }

    /** 计算结果（含计算过程，便于审计与展示）。 */
    public record Result(BigDecimal baseAmount, BigDecimal finalAmount, String explain) {
    }

    /**
     * 计算单个收费项目的金额（无规则，仅用项目默认单价）。
     */
    public Result calculate(FinFeeItem item, Context ctx) {
        return calculate(item, ctx, null);
    }

    /**
     * 计算金额（带一条计费规则）。
     *
     * @param rule 可为 null（无规则时用项目默认单价 + STANDARD）
     */
    public Result calculate(FinFeeItem item, Context ctx, FinBillingRule rule) {
        if (item == null) {
            throw BizException.paramInvalid("收费项目不能为空");
        }
        CalcMode mode;
        try {
            mode = CalcMode.valueOf(item.getCalcMode());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("计费方式不合法: " + item.getCalcMode());
        }
        RuleType ruleType = RuleType.STANDARD;
        String config = "{}";
        if (rule != null) {
            try {
                ruleType = RuleType.valueOf(rule.getRuleType());
            } catch (IllegalArgumentException e) {
                throw BizException.paramInvalid("规则类型不合法: " + rule.getRuleType());
            }
            config = rule.getPriceConfig() == null ? "{}" : rule.getPriceConfig();
        }

        // EXEMPT 直接归零
        if (ruleType == RuleType.EXEMPT) {
            return new Result(money(null), money(null), "全额减免（EXEMPT）");
        }

        BigDecimal unitPrice = item.getUnitPrice() == null
                ? BigDecimal.ZERO : item.getUnitPrice();
        // TIERED / STANDARD 可从规则里覆盖单价
        BigDecimal rulePrice = extractPrice(config);
        if (rulePrice != null) {
            unitPrice = rulePrice;
        }

        BigDecimal base = baseAmount(mode, unitPrice, ctx);
        BigDecimal finalAmt = base;
        StringBuilder why = new StringBuilder();
        why.append(mode.label()).append("：单价 ").append(unitPrice);

        switch (ruleType) {
            case STANDARD -> why.append("（标准价）");
            case TIERED -> {
                // 阶梯：按用量分段累加（用量 = 数量；面积类用面积）
                BigDecimal usage = usageOf(mode, ctx);
                BigDecimal tiered = tieredAmount(config, usage);
                if (tiered != null) {
                    base = tiered;
                    finalAmt = tiered;
                    why.append("（阶梯计价，用量 ").append(usage).append("）");
                }
            }
            case DISCOUNT -> {
                BigDecimal rate = extractRate(config);
                if (rate != null) {
                    finalAmt = base.multiply(rate).setScale(2, RoundingMode.HALF_UP);
                    why.append("（折扣 ").append(rate).append("）");
                }
            }
            default -> {
            }
        }
        return new Result(money(base), money(finalAmt), why.toString());
    }

    /** 基础金额。 */
    private BigDecimal baseAmount(CalcMode mode, BigDecimal unitPrice, Context ctx) {
        return switch (mode) {
            case FIXED, BY_HOUSE -> unitPrice;
            case BY_AREA -> {
                if (ctx == null || ctx.area() == null) {
                    throw BizException.paramInvalid("按面积计费需提供面积");
                }
                yield unitPrice.multiply(ctx.area());
            }
            case BY_PERSON, BY_BED, BY_NIGHT -> {
                if (ctx == null || ctx.quantity() == null) {
                    throw BizException.paramInvalid("按" + mode.label() + "计费需提供数量");
                }
                if (ctx.quantity() <= 0) {
                    throw BizException.paramInvalid("数量必须大于 0");
                }
                yield unitPrice.multiply(BigDecimal.valueOf(ctx.quantity()));
            }
            case METER -> {
                if (ctx == null || ctx.meterStart() == null || ctx.meterEnd() == null) {
                    throw BizException.paramInvalid("按抄表计费需提供上次与本次读数");
                }
                BigDecimal used = ctx.meterEnd().subtract(ctx.meterStart());
                if (used.compareTo(BigDecimal.ZERO) < 0) {
                    throw BizException.paramInvalid("本次读数不能小于上次读数");
                }
                yield unitPrice.multiply(used);
            }
        };
    }

    private static BigDecimal usageOf(CalcMode mode, Context ctx) {
        if (mode == CalcMode.BY_AREA && ctx != null && ctx.area() != null) {
            return ctx.area();
        }
        if (ctx != null && ctx.quantity() != null) {
            return BigDecimal.valueOf(ctx.quantity());
        }
        if (ctx != null && ctx.meterStart() != null && ctx.meterEnd() != null) {
            return ctx.meterEnd().subtract(ctx.meterStart());
        }
        return BigDecimal.ZERO;
    }

    /**
     * 阶梯计价：{@code {"tiers":[{"limit":50,"price":3.0},{"limit":null,"price":5.0}]}}
     *
     * <p>各 tier 的 {@code limit} 是<b>上限</b>（含），最后一段 {@code limit=null} 表示不封顶。
     * 用量按段累加：前 50 度 × 3，超出部分 × 5。
     */
    private BigDecimal tieredAmount(String config, BigDecimal usage) {
        List<BigDecimal[]> tiers = parseTiers(config);
        if (tiers.isEmpty()) {
            return null;
        }
        BigDecimal remain = usage;
        BigDecimal total = BigDecimal.ZERO;
        BigDecimal lower = BigDecimal.ZERO;
        for (BigDecimal[] t : tiers) {
            BigDecimal limit = t[0];
            BigDecimal price = t[1];
            BigDecimal span;
            if (limit == null) {
                span = remain;
            } else {
                span = limit.subtract(lower).min(remain);
            }
            if (span.compareTo(BigDecimal.ZERO) > 0) {
                total = total.add(span.multiply(price));
                remain = remain.subtract(span);
            }
            if (limit != null) {
                lower = limit;
            }
            if (remain.compareTo(BigDecimal.ZERO) <= 0) {
                break;
            }
        }
        return total;
    }

    /** 解析 tiers：[{limit, price}]，limit 为 null 表示不封顶。 */
    private List<BigDecimal[]> parseTiers(String config) {
        List<BigDecimal[]> out = new ArrayList<>();
        try {
            com.fasterxml.jackson.databind.JsonNode root =
                    new com.fasterxml.jackson.databind.ObjectMapper().readTree(config);
            com.fasterxml.jackson.databind.JsonNode tiers = root.get("tiers");
            if (tiers == null || !tiers.isArray()) {
                return out;
            }
            for (com.fasterxml.jackson.databind.JsonNode t : tiers) {
                com.fasterxml.jackson.databind.JsonNode lim = t.get("limit");
                com.fasterxml.jackson.databind.JsonNode pri = t.get("price");
                if (pri == null) {
                    continue;
                }
                out.add(new BigDecimal[]{
                        (lim == null || lim.isNull()) ? null : lim.decimalValue(),
                        pri.decimalValue()});
            }
        } catch (Exception e) {
            log.warn("价格配置解析失败，按无阶梯处理: {}", config);
        }
        return out;
    }

    private BigDecimal extractPrice(String config) {
        try {
            com.fasterxml.jackson.databind.JsonNode n =
                    new com.fasterxml.jackson.databind.ObjectMapper().readTree(config).get("price");
            return (n == null || n.isNull()) ? null : n.decimalValue();
        } catch (Exception e) {
            return null;
        }
    }

    private BigDecimal extractRate(String config) {
        try {
            com.fasterxml.jackson.databind.JsonNode n =
                    new com.fasterxml.jackson.databind.ObjectMapper().readTree(config).get("rate");
            return (n == null || n.isNull()) ? null : n.decimalValue();
        } catch (Exception e) {
            return null;
        }
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
