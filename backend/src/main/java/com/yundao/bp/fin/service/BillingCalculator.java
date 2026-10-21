package com.yundao.bp.fin.service;

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
