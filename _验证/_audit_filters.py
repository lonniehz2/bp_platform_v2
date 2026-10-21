# -*- coding: utf-8 -*-
"""列表页筛选现状普查

对每个 views/*.vue 判定：
  · 是否有表格
  · 是否有搜索/筛选输入（placeholder 或 el-select 作筛选）
  · 是否有「查询」按钮
  · 是否有「清空/重置」按钮
据此排出改造优先级。
"""
import io
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')


def analyze(src):
    has_table = '<el-table' in src
    # 筛选输入：toolbar 里有 placeholder 的输入框
    tb = re.search(r'<div class="toolbar">(.*?)</div>', src, re.S)
    scope = tb.group(1) if tb else ''
    inputs = re.findall(r'<el-input[^>]*placeholder="([^"]*)"', scope)
    selects = re.findall(r'<el-select[^>]*placeholder="([^"]*)"', scope)
    datepickers = re.findall(r'<el-date-picker', scope)
    has_query_btn = bool(re.search(r'>\s*查询\s*<', scope))
    has_reset = bool(re.search(r'>\s*(清空|重置)\s*<', scope))
    return {
        'table': has_table,
        'inputs': inputs,
        'selects': selects,
        'dates': len(datepickers),
        'query': has_query_btn,
        'reset': has_reset,
    }


rows = []
for fn in sorted(os.listdir(ROOT)):
    if not fn.endswith('.vue'):
        continue
    src = io.open(os.path.join(ROOT, fn), encoding='utf-8').read()
    a = analyze(src)
    if not a['table']:
        continue
    cond = len(a['inputs']) + len(a['selects']) + a['dates']
    rows.append((fn, cond, a['query'], a['reset'], len(a['inputs']), len(a['selects']), a['dates']))

full = [r for r in rows if r[2] and r[3]]
part = [r for r in rows if r[2] and not r[3]]
none = [r for r in rows if not r[2]]

print('列表页共 %d 个' % len(rows))
print('\n【A】有查询 + 有清空：%d 个' % len(full))
for r in full:
    print('   %-24s 条件 %d（输入 %d/下拉 %d/日期 %d）' % (r[0], r[1], r[4], r[5], r[6]))

print('\n【B】有查询、缺清空：%d 个  ← 本轮重点' % len(part))
for r in part:
    print('   %-24s 条件 %d（输入 %d/下拉 %d/日期 %d）' % (r[0], r[1], r[4], r[5], r[6]))

print('\n【C】没有查询按钮：%d 个  ← 需要补筛选' % len(none))
for r in none:
    print('   %-24s 条件 %d（输入 %d/下拉 %d/日期 %d）' % (r[0], r[1], r[4], r[5], r[6]))
