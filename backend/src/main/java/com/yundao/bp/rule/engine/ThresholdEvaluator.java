package com.yundao.bp.rule.engine;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import org.springframework.stereotype.Component;

/**
 * 阈值求值器（规则引擎的<b>纯函数内核</b>）。
 *
 * <p><b>为什么单独抽出来</b>：阈值判断是规则引擎最容易出错、也最需要
 * 「自设阈值」灵活性的部分。抽成纯函数后可以穷举测试，不必依赖数据库。
 *
 * <p>支持的规则类型：
 * <ul>
 *   <li>{@code THRESHOLD} 单阈值：value OP threshold，OP ∈ &gt; &gt;= &lt; &lt;= == !=</li>
 *   <li>{@code TIME_WINDOW} 时间窗统计：windowMinutes 内出现 countThreshold 次</li>
 *   <li>{@code RATIO} 比例阈值：ratio = part/total，超过 ratioThreshold 命中</li>
 *   <li>{@code DURATION} 持续时长：持续 minutes 分钟仍处于该状态</li>
 *   <li>{@code EVENT_MATCH} 事件匹配：eventType 属于 events 列表</li>
 * </ul>
 *
 * <p>阈值配置示例（存 `threshold_json`）：
 * <pre>
 * {"op": "&gt;", "value": 3}
 * {"windowMinutes": 30, "countThreshold": 5}
 * {"ratioThreshold": 0.2}
 * {"durationMinutes": 120}
 * {"events": ["access.duress", "device.offline"]}
 * </pre>
 */
@Component
public class ThresholdEvaluator {

    private static final ObjectMapper JSON = new ObjectMapper();

    /**
     * 求值结果。
     *
     * @param hit     是否命中
     * @param actual  实际值（用于告警正文与留痕）
     * @param explain 判定说明（为什么命中/未命中）
     */
    public record Result(boolean hit, BigDecimal actual, String explain) {
        public static Result of(boolean hit, BigDecimal actual, String explain) {
            return new Result(hit, actual, explain);
        }
    }

    /**
     * 按规则类型求值。
     *
     * @param ruleType      规则类型
     * @param thresholdJson 阈值配置
     * @param actual        实测值（THRESHOLD/RATIO/DURATION 用）
     * @param count         命中次数（TIME_WINDOW 用）
     * @param eventType     事件类型（EVENT_MATCH 用）
     * @param total         总量（RATIO 用，可空）
     */
    public Result evaluate(String ruleType, String thresholdJson, BigDecimal actual,
                           Integer count, String eventType, BigDecimal total) {
        String type = ruleType == null ? "THRESHOLD" : ruleType.trim().toUpperCase();
        JsonNode cfg;
        try {
            cfg = (thresholdJson == null || thresholdJson.isBlank())
                    ? JSON.createObjectNode() : JSON.readTree(thresholdJson);
        } catch (Exception e) {
            return Result.of(false, actual,
                    "阈值配置非法 JSON，规则被跳过：" + e.getMessage());
        }
        return switch (type) {
            case "THRESHOLD" -> threshold(cfg, actual);
            case "TIME_WINDOW" -> timeWindow(cfg, count, actual);
            case "RATIO" -> ratio(cfg, actual, total);
            case "DURATION" -> duration(cfg, actual);
            case "EVENT_MATCH" -> eventMatch(cfg, eventType);
            default -> Result.of(false, actual, "未知规则类型：" + type);
        };
    }

    // ---------- THRESHOLD ----------

    private Result threshold(JsonNode cfg, BigDecimal actual) {
        if (actual == null) {
            return Result.of(false, null, "未提供实测值，无法判定");
        }
        String op = cfg.hasNonNull("op") ? cfg.get("op").asText() : ">";
        BigDecimal th = cfg.hasNonNull("value")
                ? new BigDecimal(cfg.get("value").asText()) : BigDecimal.ZERO;
        int cmp = actual.compareTo(th);
        boolean hit = switch (op) {
            case ">" -> cmp > 0;
            case ">=" -> cmp >= 0;
            case "<" -> cmp < 0;
            case "<=" -> cmp <= 0;
            case "==", "=" -> cmp == 0;
            case "!=", "<>" -> cmp != 0;
            default -> false;
        };
        return Result.of(hit, actual, "实测 " + plain(actual) + " " + op + " 阈值 "
                + plain(th) + (hit ? " → 命中" : " → 未命中"));
    }

    // ---------- TIME_WINDOW ----------

    private Result timeWindow(JsonNode cfg, Integer count, BigDecimal actual) {
        int need = cfg.hasNonNull("countThreshold")
                ? cfg.get("countThreshold").asInt() : 1;
        int win = cfg.hasNonNull("windowMinutes")
                ? cfg.get("windowMinutes").asInt() : 0;
        int c = count == null ? (actual == null ? 0 : actual.intValue()) : count;
        boolean hit = c >= need;
        return Result.of(hit, BigDecimal.valueOf(c),
                win > 0 ? (win + " 分钟内发生 " + c + " 次，阈值 " + need + " 次"
                        + (hit ? " → 命中" : " → 未命中"))
                        : ("累计 " + c + " 次，阈值 " + need + " 次"
                                + (hit ? " → 命中" : " → 未命中")));
    }

    // ---------- RATIO ----------

    private Result ratio(JsonNode cfg, BigDecimal part, BigDecimal total) {
        BigDecimal t = total;
        if (t == null && cfg.hasNonNull("total")) {
            t = new BigDecimal(cfg.get("total").asText());
        }
        if (part == null || t == null || t.compareTo(BigDecimal.ZERO) == 0) {
            return Result.of(false, null, "比例计算缺少分母或分子，跳过（避免除零）");
        }
        BigDecimal r = part.divide(t, 4, RoundingMode.HALF_UP);
        BigDecimal th = cfg.hasNonNull("ratioThreshold")
                ? new BigDecimal(cfg.get("ratioThreshold").asText())
                : new BigDecimal("0.2");
        boolean hit = r.compareTo(th) >= 0;
        return Result.of(hit, r, "占比 " + r.multiply(BigDecimal.valueOf(100))
                .setScale(2, RoundingMode.HALF_UP) + "% "
                + (hit ? "≥" : "<") + " 阈值 "
                + th.multiply(BigDecimal.valueOf(100))
                .setScale(2, RoundingMode.HALF_UP) + "%"
                + (hit ? " → 命中" : " → 未命中"));
    }

    // ---------- DURATION ----------

    private Result duration(JsonNode cfg, BigDecimal minutes) {
        if (minutes == null) {
            return Result.of(false, null, "未提供持续时长，无法判定");
        }
        int need = cfg.hasNonNull("durationMinutes")
                ? cfg.get("durationMinutes").asInt() : 60;
        boolean hit = minutes.compareTo(BigDecimal.valueOf(need)) >= 0;
        return Result.of(hit, minutes, "已持续 " + plain(minutes) + " 分钟，阈值 "
                + need + " 分钟" + (hit ? " → 命中" : " → 未命中"));
    }

    // ---------- EVENT_MATCH ----------

    private Result eventMatch(JsonNode cfg, String eventType) {
        if (eventType == null) {
            return Result.of(false, null, "未提供事件类型，无法判定");
        }
        if (!cfg.has("events") || !cfg.get("events").isArray()) {
            return Result.of(false, null, "阈值配置缺少 events 数组，规则被跳过");
        }
        boolean found = false;
        for (JsonNode n : cfg.get("events")) {
            String e = n.asText();
            if (e.equals(eventType)) {
                found = true;
                break;
            }
            // 支持前缀通配：access.*
            if (e.endsWith("*") && eventType.startsWith(e.substring(0, e.length() - 1))) {
                found = true;
                break;
            }
        }
        return Result.of(found, null, "事件 " + eventType
                + (found ? " 在告警事件清单内 → 命中" : " 不在清单内 → 未命中"));
    }

    private static String plain(BigDecimal v) {
        return v == null ? "-" : v.stripTrailingZeros().toPlainString();
    }

    /** 便捷方法：单阈值判定。 */
    public boolean over(BigDecimal actual, String op, BigDecimal threshold) {
        String cfg = "{\"op\":\"" + op + "\",\"value\":" + threshold.toPlainString() + "}";
        return evaluate("THRESHOLD", cfg, actual, null, null, null).hit();
    }

    /** 列出支持的规则类型（供前端下拉与字典对齐）。 */
    public List<String> supportedTypes() {
        return List.of("THRESHOLD", "TIME_WINDOW", "RATIO", "DURATION", "EVENT_MATCH");
    }
}
