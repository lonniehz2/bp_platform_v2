# -*- coding: utf-8 -*-
"""重新生成 EnumLabels.java（带正确引号）"""
import io
import re

FE = r'D:\Work\业务平台开发\frontend\src\constants\enums.js'
OUT = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
       r'\common\util\EnumLabels.java')

es = io.open(FE, encoding='utf-8').read()
m = re.search(r'const GLOBAL = \{(.*?)\n\}', es, re.S)
pairs = re.findall(r"^\s*'?([A-Z][A-Z_0-9]*)'?:\s*'([^']+)'", m.group(1), re.M)

seen = {}
order = []
for k, v in pairs:
    if k not in seen:
        seen[k] = v
        order.append(k)

lines = ',\n'.join('            new String[]{"%s", "%s"}' % (k, seen[k]) for k in order)

TMPL = '''package com.yundao.bp.common.util;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 枚举值 → 中文标签（全局扁平表）。
 *
 * <p>与前端 {@code constants/enums.js} 保持同一份数据：绝大多数枚举码全局唯一，
 * 一张表即可覆盖全部业务字段，无需按字段维护类型映射。</p>
 *
 * <p>用途：报表/CSV 导出、以及 {@code DisplayEnricher} 为列表接口补 xxxLabel，
 * 避免界面上出现 ALLOCATED、PUBLIC_RENTAL 这类内部编码。</p>
 */
public final class EnumLabels {

    private EnumLabels() {
    }

    private static final Map<String, String> GLOBAL = new HashMap<>();

    static {
        List<String[]> pairs = List.of(
%s
        );
        for (String[] p : pairs) {
            GLOBAL.put(p[0], p[1]);
        }
    }

    /** 少数同名不同义的值，按字段名覆盖 */
    private static final Map<String, Map<String, String>> OVERRIDE = Map.of(
            "dunningType", Map.of("VISIT", "上门", "PHONE", "电话"),
            "visitStatus", Map.of("VISIT", "来访"),
            "flowType", Map.of("IN", "收入", "OUT", "支出"),
            "auditLevel", Map.of("INFO", "提示", "WARNING", "警告", "CRITICAL", "严重"),
            "alertLevel", Map.of("INFO", "提示", "WARNING", "警告", "CRITICAL", "严重"),
            "creditLevel", Map.of("MINOR", "轻微", "MAJOR", "较重", "SEVERE", "严重")
    );

    /**
     * @param field 字段名（用于同名覆盖，可为 null）
     * @param value 原始值
     */
    public static String of(String field, Object value) {
        if (value == null) {
            return "";
        }
        String v = String.valueOf(value);
        if (v.isBlank()) {
            return "";
        }
        if (field != null && OVERRIDE.containsKey(field)) {
            String hit = OVERRIDE.get(field).get(v);
            if (hit != null) {
                return hit;
            }
        }
        return GLOBAL.getOrDefault(v, v);
    }
}
''' % lines

io.open(OUT, 'w', encoding='utf-8').write(TMPL)
print('  ✓ EnumLabels.java 重新生成：%d 条' % len(seen))
