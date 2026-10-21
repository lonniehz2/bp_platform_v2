# -*- coding: utf-8 -*-
"""① 从 enums.js 生成 Java 全量枚举表 ② 修 ID 字符串判定"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src\constants\enums.js'
JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ---------- 1) 解析前端 GLOBAL 映射 ----------
es = io.open(FE, encoding='utf-8').read()
m = re.search(r'const GLOBAL = \{(.*?)\n\}', es, re.S)
body = m.group(1)
pairs = re.findall(r"^\s*'?([A-Z][A-Z_0-9]*)'?:\s*'([^']+)'", body, re.M)
# 去重（同名取第一次）
seen = {}
order = []
for k, v in pairs:
    if k not in seen:
        seen[k] = v
        order.append(k)
print('  从 enums.js 解析出 %d 个枚举' % len(seen))

entries = ',\n'.join('            "%s", "%s"' % (k, seen[k]) for k in order)

UTIL = '''package com.yundao.bp.common.util;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 枚举值 → 中文标签（全局扁平表）。
 *
 * <p>与前端 {@code constants/enums.js} 保持一致：绝大多数枚举码全局唯一，
 * 因此用一张表即可覆盖全部业务字段，无需按字段维护类型映射。</p>
 *
 * <p>用途：报表导出、CSV、以及 {@code DisplayEnricher} 给列表接口补 xxxLabel。</p>
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
''' % entries

io.open(os.path.join(JAVA, 'common', 'util', 'EnumLabels.java'), 'w',
        encoding='utf-8').write(UTIL)
print('  ✓ 重新生成 EnumLabels.java（%d 条映射）' % len(seen))

# ---------- 2) DisplayEnricher：ID 支持字符串 ----------
P = os.path.join(JAVA, 'common', 'web', 'DisplayEnricher.java')
s = io.open(P, encoding='utf-8').read()

old = '''            if (key.endsWith("Id") && v instanceof Number n) {
                String name = nameOf(key, n.longValue());
                if (name != null && !name.isBlank()) {
                    extra.put(key + "Name", name);
                }
            } else if (v instanceof String s && !s.isBlank() && isEnumField(key)) {'''
new = '''            Long idValue = asLong(v);
            if (key.endsWith("Id") && idValue != null) {
                // 注意：本项目 Long 统一序列化为字符串，因此不能只判断 Number
                String name = nameOf(key, idValue);
                if (name != null && !name.isBlank()) {
                    extra.put(key + "Name", name);
                }
            } else if (v instanceof String s && !s.isBlank() && isEnumField(key)) {'''
assert old in s
s = s.replace(old, new, 1)

# 增加 asLong 辅助
s = s.replace('''    private String nameOf(String key, long id) {''',
              '''    /** 兼容 Number 与「纯数字字符串」两种形态 */
    private static Long asLong(Object v) {
        if (v instanceof Number n) {
            return n.longValue();
        }
        if (v instanceof String str && !str.isBlank()) {
            String t = str.trim();
            boolean digits = true;
            for (int i = 0; i < t.length(); i++) {
                if (!Character.isDigit(t.charAt(i))) {
                    digits = false;
                    break;
                }
            }
            if (digits && t.length() <= 20) {
                try {
                    return Long.parseLong(t);
                } catch (NumberFormatException ignore) {
                    return null;
                }
            }
        }
        return null;
    }

    private String nameOf(String key, long id) {''', 1)

# 枚举判定：交给 EnumLabels 全量表，去掉「必须变化才加」的限制（中文原样也可）
s = s.replace('''                String label = EnumLabels.of(FIELD_ENUM_TYPE.get(key), s);
                if (label != null && !label.equals(s)) {
                    extra.put(key + "Label", label);
                }''',
              '''                String label = EnumLabels.of(key, s);
                if (label != null && !label.equals(s)) {
                    extra.put(key + "Label", label);
                }''', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ DisplayEnricher：支持字符串 ID + 全局枚举表')
