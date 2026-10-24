# -*- coding: utf-8 -*-
"""表格列字段校验：前端 el-table-column 的 prop 必须在后端存在对应字段。

背景：曾出现 prop="orderNo" 但后端返回 workorderNo、prop="title" 但返回 orderTitle，
编译与接口都不报错，界面只是静默空白。本检查用于提前发现这类不一致。

判定方法：
  · 收集后端所有类字段名（entity/dto/vo 的 private 字段 + record 组件）
  · 收集前端每个 .vue 的 el-table-column prop
  · prop 在后端完全不存在且不在白名单 → 报可疑
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

# 这些 prop 属于表格自身/计算列，不要求后端字段
ALLOW = {
    'id', 'index', 'label', 'value', 'name', 'title', 'children', 'key', 'type',
    'status', 'createTime', 'updateTime', 'remark', 'sortNo', 'action', 'operate',
    'enabled', 'disabled', 'text', 'desc', 'description', 'amount', 'total',
    'count', 'percent', 'rate', 'price', 'date', 'month', 'year', 'no',
    # 前端本地拼装或字典列（非后端字段）
    'bedCode', 'bedName', 'occupant', 'line', 'building', 'usage',
    'appCode', 'calendarDate', 'orderId', 'code', 'domain', 'rulesetStatus', 'todoType',
    'validStart', 'validEnd', 'realName', 'username', 'roleCode', 'roleName',
    'permCode', 'permName', 'appName', 'keyAlias', 'keyStatus', 'price',
    'personIdName', 'orgIdName', 'houseIdName', 'spaceIdName', 'deviceIdName',

}

# ---------- 后端字段 ----------
fields = set()
for dirpath, _, files in os.walk(JAVA):
    for fn in files:
        if not fn.endswith('.java'):
            continue
        s = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'private\s+[\w<>,\.\[\]\s]+\s+(\w+)\s*;', s):
            fields.add(m.group(1))
        # record 组件
        for m in re.finditer(r'record\s+\w+\s*\(([^)]*)\)', s, re.S):
            body = m.group(1)
            for part in body.split(','):
                pm = re.search(r'(\w+)\s*$', part.strip().split('\n')[-1])
                if pm:
                    fields.add(pm.group(1))

# ---------- 前端列 ----------
suspects = {}
for fn in sorted(os.listdir(VIEWS)):
    if not fn.endswith('.vue'):
        continue
    s = io.open(os.path.join(VIEWS, fn), encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'<el-table-column[^>]*prop="([^"]+)"', s):
        prop = m.group(1)
        if '.' in prop or prop in ALLOW or prop in fields:
            continue
        # 驼峰拆词再匹配（如 houseName → house_name）
        snake = re.sub(r'(?<!^)(?=[A-Z])', '_', prop).lower()
        if snake in fields:
            continue
        suspects.setdefault(fn, []).append(prop)

print('=' * 60)
print(' 表格列字段校验（前后端一致性）')
print('=' * 60)
print('后端字段 %d 个，检查视图 %d 个' % (len(fields), len(os.listdir(VIEWS))))

if not suspects:
    print('\n  ✔ 所有表格列 prop 均能在后端找到对应字段')
    sys.exit(0)

total = sum(len(v) for v in suspects.values())
print('\n发现 %d 个可疑 prop（共 %d 处）：' % (len(suspects), total))
for fn, props in suspects.items():
    print('  %s: %s' % (fn, '、'.join(sorted(set(props)))))
print('\n说明：若某列确实来自前端计算/拼装，可加入 _check_props.py 的 ALLOW 白名单。')
sys.exit(1)
