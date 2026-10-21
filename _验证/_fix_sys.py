# -*- coding: utf-8 -*-
"""修复：审计 JSON 列合法化 + bp_sys_config 加入租户忽略表"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ---------- 1) 审计：把 before/after 包成合法 JSON 对象 ----------
p1 = os.path.join(BASE, r'sys\audit\AuditAspect.java')
s1 = io.open(p1, encoding='utf-8').read()

old = '''                    audit.action() + (success ? "" : "（失败）"),
                    success ? null : args,
                    result,
                    null, clientIp());'''
new = '''                    audit.action() + (success ? "" : "（失败）"),
                    success ? null : wrapJson(args),
                    success ? wrapJson(result) : writeFailJson(result),
                    null, clientIp());'''
assert old in s1, '审计锚点缺失'
s1 = s1.replace(old, new, 1)

# 增加 JSON 包装方法
anchor = '''    private static String truncate(String s) {'''
helper = '''    /**
     * 把任意文本包装成<b>合法 JSON 对象</b>。
     *
     * <p>为什么需要：`bp_sys_audit_log.before_json/after_json` 是 MySQL JSON 列，
     * 直接写入被截断的 JSON 串会报 `Invalid JSON text`，导致审计丢失。
     * 统一包成 `{"text": "..."}` 可保证合法，同时保留可读内容。
     */
    private static String wrapJson(String s) {
        if (s == null) {
            return null;
        }
        try {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("text", truncate(s));
            return JSON.writeValueAsString(m);
        } catch (Exception e) {
            return null;
        }
    }

    /** 失败信息包装（含异常原文）。 */
    private static String writeFailJson(String s) {
        try {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("error", truncate(s));
            return JSON.writeValueAsString(m);
        } catch (Exception e) {
            return null;
        }
    }

''' + anchor
assert anchor in s1
s1 = s1.replace(anchor, helper, 1)
io.open(p1, 'w', encoding='utf-8').write(s1)
print('  ✓ 审计 JSON 列写入已合法化')

# ---------- 2) bp_sys_config 加入租户忽略表 ----------
p2 = os.path.join(BASE, r'common\config\MybatisTenantConfig.java')
s2 = io.open(p2, encoding='utf-8').read()
if 'bp_sys_config' not in s2:
    s2 = s2.replace('"bp_sys_dict",          // 系统内置字典',
                    '"bp_sys_dict",          // 系统内置字典\n'
                    '            "bp_sys_config",        // 系统参数（全局默认 + 租户覆盖，'
                    '由 ConfigService 自行合并，不能加租户过滤）')
    io.open(p2, 'w', encoding='utf-8').write(s2)
    print('  ✓ bp_sys_config 已加入租户忽略表')
else:
    print('  - bp_sys_config 已在忽略表')
