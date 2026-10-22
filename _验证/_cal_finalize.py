# -*- coding: utf-8 -*-
"""日房态宫格收尾：分页只在明细视图显示；radio 用 value 替代 label。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'HouseCalendar.vue')
s = io.open(P, encoding='utf-8').read()

pairs = [
    ('<el-radio-button label="grid">月历</el-radio-button>',
     '<el-radio-button value="grid">月历</el-radio-button>'),
    ('<el-radio-button label="table">明细</el-radio-button>',
     '<el-radio-button value="table">明细</el-radio-button>'),
    ('<el-pagination style="margin-top:12px"',
     '<el-pagination v-if="viewMode === \'table\'" style="margin-top:12px"'),
]
n = 0
for a, b in pairs:
    if a in s:
        s = s.replace(a, b, 1)
        n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已应用 %d 处修改' % n)
