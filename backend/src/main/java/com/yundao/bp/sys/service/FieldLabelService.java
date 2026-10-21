package com.yundao.bp.sys.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 字段中文名字典。
 *
 * <p>数据来源：MySQL {@code information_schema.columns.column_comment}。
 * 本项目 DDL 要求列注释 100% 覆盖（有校验脚本保证），因此可以直接
 * 用「列注释」当字段中文名，**新增字段无需改前端字典**。</p>
 *
 * <p>同时做 camelCase ↔ snake_case 双向对齐，前端按 camelCase 取用。</p>
 */
@Service
public class FieldLabelService {

    private final JdbcTemplate jdbcTemplate;

    /** 简单缓存：字典不常变化，进程内缓存足够 */
    private volatile Map<String, String> cache;

    public FieldLabelService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public Map<String, String> labels() {
        Map<String, String> local = cache;
        if (local != null) {
            return local;
        }
        synchronized (this) {
            if (cache != null) {
                return cache;
            }
            Map<String, String> map = new HashMap<>(4096);
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                    "SELECT column_name AS cn, column_comment AS cc "
                            + "FROM information_schema.columns "
                            + "WHERE table_schema = DATABASE() "
                            + "AND column_comment IS NOT NULL AND column_comment <> ''");
            for (Map<String, Object> r : rows) {
                String col = String.valueOf(r.get("cn"));
                String comment = String.valueOf(r.get("cc"));
                if (comment.isBlank()) {
                    continue;
                }
                // 列注释常写成「发放方式：FINANCE 财政直发 / BANK 银行代发」，
                // 作为表单标签只需要冒号前的主名；括号里的单位同理去掉。
                String label = comment;
                int cut = indexOfAny(label, '：', ':', '（', '(');
                if (cut > 0) {
                    label = label.substring(0, cut);
                }
                label = label.trim();
                if (label.isBlank()) {
                    label = comment;
                }
                String camel = toCamel(col);
                // 同一 camel 名可能来自多张表：优先保留更短/更具体的注释
                map.merge(camel, label,
                        (a, b) -> a.length() <= b.length() ? a : b);
            }
            cache = map;
            return map;
        }
    }

    /** 失效缓存（DDL 变更后调用） */
    public void refresh() {
        cache = null;
    }

    private static int indexOfAny(String s, char... chars) {
        int best = -1;
        for (char c : chars) {
            int i = s.indexOf(c);
            if (i > 0 && (best < 0 || i < best)) {
                best = i;
            }
        }
        return best;
    }

    private static String toCamel(String snake) {
        StringBuilder sb = new StringBuilder(snake.length());
        boolean upper = false;
        for (int i = 0; i < snake.length(); i++) {
            char c = snake.charAt(i);
            if (c == '_') {
                upper = true;
                continue;
            }
            sb.append(upper ? Character.toUpperCase(c) : c);
            upper = false;
        }
        return sb.toString();
    }
}
