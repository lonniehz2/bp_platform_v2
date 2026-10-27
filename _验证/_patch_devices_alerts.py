# -*- coding: utf-8 -*-
"""设备告警弹窗：级别中文 + 详情 JSON 可读化。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'Devices.vue')
s = io.open(p, encoding='utf-8').read()

old_level = '''        <el-table-column prop="eventLevel" label="级别" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.eventLevel === 'CRITICAL' ? 'danger'
              : (row.eventLevel === 'WARN' ? 'warning' : 'info')">
              {{ row.eventLevel }}
            </el-tag>
          </template>
        </el-table-column>'''

new_level = '''        <el-table-column prop="eventLevel" label="级别" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="levelTagType(row.eventLevel)">
              {{ levelLabel(row.eventLevel) }}
            </el-tag>
          </template>
        </el-table-column>'''

if old_level in s:
    s = s.replace(old_level, new_level, 1)
else:
    print('级别列未匹配，尝试宽松替换')
    s = s.replace('{{ row.eventLevel }}', '{{ levelLabel(row.eventLevel) }}', 1)

old_body = '''        <el-table-column prop="body" label="详情" min-width="200" show-overflow-tooltip />'''
new_body = '''        <el-table-column prop="body" label="详情" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ fmtEventBody(row.body) }}</template>
        </el-table-column>'''
if old_body in s:
    s = s.replace(old_body, new_body, 1)
else:
    print('详情列未匹配')

if "from '@/utils/eventDisplay'" not in s:
    s = s.replace("import { enumLabel } from '@/constants/enums'",
                  "import { enumLabel } from '@/constants/enums'\n"
                  "import { levelLabel, levelTagType, fmtEventBody } from '@/utils/eventDisplay'", 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('Devices 告警弹窗已更新')
