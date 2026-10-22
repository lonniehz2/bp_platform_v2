# -*- coding: utf-8 -*-
"""合同列表：
1. 操作列真正加入「详情」「编辑」（上次锚点未匹配，按钮没插进去）
2. 收敛列宽、合并起止租期、去掉签约时间列（详情里看），减少横向滚动
3. 表格固定高度 + 固定操作列，滚动更自然
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Contracts.vue')

s = io.open(P, encoding='utf-8').read()
changed = []

# 1) 起租/止租 两列合并为「租期」，去掉签约时间列
old_range = '''<el-table-column prop="leaseStart" label="起租" width="105" />
          <el-table-column prop="leaseEnd" label="止租" width="105" />'''
new_range = '''<el-table-column label="租期" width="200">
            <template #default="{ row }">
              {{ row.leaseStart }} ~ {{ row.leaseEnd }}
              <span class="muted" style="font-size:12px">({{ row.leaseMonths }} 个月)</span>
            </template>
          </el-table-column>'''
if old_range in s:
    s = s.replace(old_range, new_range, 1)
    changed.append('合并租期')

s = re.sub(r'\s*<el-table-column prop="signTime" label="签约时间"[^/]*/>', '', s)

# 2) 收敛列宽
s = s.replace('<el-table-column prop="contractNo" label="合同号" width="170" />',
              '<el-table-column prop="contractNo" label="合同号" width="165" show-overflow-tooltip />', 1)
s = s.replace('<el-table-column label="合同类型" width="120">',
              '<el-table-column label="类型" width="100">', 1)
s = s.replace('<el-table-column prop="depositAmount" label="押金" width="95" />',
              '<el-table-column prop="depositAmount" label="押金" width="90" />', 1)
s = s.replace('<el-table-column label="到期" width="100">',
              '<el-table-column label="到期" width="90">', 1)
s = s.replace('<el-table-column prop="contractStatusLabel" label="状态" width="105">',
              '<el-table-column label="状态" width="100">', 1)

# 3) 表格固定高度 + 固定操作列
s = s.replace('<el-table :data="rows" v-loading="loading" border size="small">',
              '<el-table :data="rows" v-loading="loading" border size="small" max-height="560">', 1)

# 4) 操作列：真正插入「详情」「编辑」，并收窄宽度
s = s.replace('<el-table-column label="操作" width="380" fixed="right">',
              '<el-table-column label="操作" width="300" fixed="right">', 1)
m = re.search(r'(<el-table-column label="操作" width="300" fixed="right">\s*\n\s*<template #default="\{ row \}">)', s)
if m and 'openContractDetail(row)' not in s:
    ins = m.group(1) + '''
            <el-button link type="primary" @click="openContractDetail(row)"
                       data-testid="contract-detail">详情</el-button>
            <el-button link type="warning" :disabled="row.contractStatus !== 'DRAFT'"
                       @click="openContractEdit(row)"
                       data-testid="contract-edit">编辑</el-button>'''
    s = s[:m.start()] + ins + s[m.end():]
    changed.append('详情/编辑按钮')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已改：', '、'.join(changed) if changed else '（无匹配）')
print('详情按钮存在:', 'openContractDetail(row)' in s)
