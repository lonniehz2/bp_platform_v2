# -*- coding: utf-8 -*-
"""列表可读性：补空状态引导、合同电话/组织列、设备组织列。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

EMPTY = {
    'Contracts.vue': '暂无合同，点右上「新建合同」或「快捷签约」',
    'Devices.vue': '暂无设备，可点「同步设备」从 IoT 拉取',
    'Applications.vue': '暂无申请单，点右上「新建申请」',
    'Waitlist.vue': '轮候库为空，审核通过后会自动入队',
    'Publicities.vue': '暂无公示，配租/资格公示从这里发起',
    'Keyring.vue': '暂无钥匙，先在「人员档案」建档再入包',
    'Grants.vue': '暂无授权记录',
    'Arrears.vue': '暂无欠费记录',
    'Allocations.vue': '暂无配租单，摇号完成后点「生成配租单」',
    'DevCommands.vue': '暂无设备指令',
    'DevEvents.vue': '暂无设备事件',
    'MeterReadings.vue': '暂无抄表记录，可人工录入或从 IoT 拉取',
}

for fname, text in EMPTY.items():
    p = os.path.join(VIEWS, fname)
    if not os.path.exists(p):
        print('跳过(不存在)', fname)
        continue
    s = io.open(p, encoding='utf-8').read()
    if 'empty-text' in s:
        print('已有空状态', fname)
        continue
    # 给第一个 el-table 加 empty-text
    m = re.search(r'<el-table\b([^>]*)>', s)
    if not m:
        print('未找到表格', fname)
        continue
    tag = m.group(0)
    new_tag = tag.replace('<el-table', '<el-table empty-text="%s"' % text, 1)
    s = s.replace(tag, new_tag, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('空状态已加', fname)

# 合同：联系电话 + 组织
p = os.path.join(VIEWS, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
if 'label="联系电话"' not in s:
    s = s.replace('''        <el-table-column prop="lesseeName" label="承租人" width="100" />''',
                  '''        <el-table-column prop="lesseeName" label="承租人" width="100" />
        <el-table-column prop="lesseePhone" label="联系电话" width="120" />
        <el-table-column label="组织" width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>
        </el-table-column>''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('合同列已补')

# 设备：组织
p2 = os.path.join(VIEWS, 'Devices.vue')
t = io.open(p2, encoding='utf-8').read()
if 'label="组织"' not in t:
    t = t.replace('''      <el-table-column prop="spaceId" label="空间" width="140">''',
                  '''      <el-table-column label="组织" width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>
      </el-table-column>
      <el-table-column prop="spaceId" label="空间" width="140">''', 1)
    io.open(p2, 'w', encoding='utf-8', newline='').write(t)
    print('设备组织列已补')
