# -*- coding: utf-8 -*-
"""房源台账前端：增加「业态」筛选（宿舍/公寓/酒店民宿/公租房…）。

与后端 houseType 参数联动，实现多业态按类型隔离查看。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Houses.vue')
s = io.open(P, encoding='utf-8').read()

# 1) 工具栏加业态下拉（放在状态下拉之后）
if 'houseTypeFilter' not in s:
    m = re.search(r'(<el-select v-model="houseStatus"[\s\S]{0,220}?</el-select>)', s)
    if m:
        add = m.group(1) + '''
        <el-select v-model="houseTypeFilter" placeholder="业态" clearable
                   style="width:150px" @change="reload" data-testid="house-type-filter">
          <el-option v-for="t in houseTypes" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>'''
        s = s[:m.start()] + add + s[m.end():]
        print('工具栏已加业态下拉')

    # 2) 状态与类型清单
    anchor = "const houseStatus = ref('')"
    extra = anchor + '''
const houseTypeFilter = ref('')
/** 多业态房源类型（宿舍/公寓/酒店民宿 与保障房并行） */
const houseTypes = [
  { value: 'PUBLIC_RENTAL', label: '公租房' },
  { value: 'AFFORDABLE_RENTAL', label: '经适房' },
  { value: 'TALENT', label: '人才房' },
  { value: 'APARTMENT', label: '公寓' },
  { value: 'DORMITORY', label: '宿舍' },
  { value: 'RENTAL', label: '租赁住房' },
  { value: 'HOTEL', label: '酒店/民宿' }
]'''
    s = s.replace(anchor, extra, 1)

    # 3) 请求带 houseType
    s = s.replace("houseStatus: houseStatus.value || undefined",
                  "houseStatus: houseStatus.value || undefined,\n      houseType: houseTypeFilter.value || undefined", 1)

    # 4) 清空
    s = s.replace("houseStatus.value = ''", "houseStatus.value = ''\n  houseTypeFilter.value = ''", 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Houses.vue 已加业态筛选')
