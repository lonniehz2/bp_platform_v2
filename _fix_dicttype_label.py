# -*- coding: utf-8 -*-
"""字典类型码 → 中文名（SysAdmin 下拉用）"""
import io
import re

FE = r'D:\Work\业务平台开发\frontend\src'
E = r'D:\Work\业务平台开发\frontend\src\constants\enums.js'
s = io.open(E, encoding='utf-8').read()

if 'DICT_TYPE_LABEL' not in s:
    s = s.rstrip() + '''

/**
 * 字典类型码 → 中文名（系统支撑页的字典类型下拉用）。
 * 与 bp_sys_dict.dict_type 一一对应。
 */
export const DICT_TYPE_LABEL = {
  HOUSE_TYPE: '房源类型',
  SECURITY_TYPE: '保障类型',
  TERMINATION_TYPE: '退租类型',
  VIOLATION_TYPE: '违规类型',
  SANCTION_TYPE: '惩戒类型',
  APPEAL_BIZ_TYPE: '申诉业务类型',
  GOV_SYSTEM_TYPE: '政务系统类型',
  GOV_REPORT_TYPE: '报送类型',
  GOV_REPORT_MODE: '报送方式',
  GOV_REPORT_CYCLE: '报送周期',
  GOV_TASK_STATUS: '报送任务状态',
  GOV_AUTH_TYPE: '政务鉴权类型',
  GOV_DEGRADE_MODE: '降级模式',
  OPEN_APP_TYPE: '开放应用类型',
  OPEN_APP_STATUS: '开放应用状态',
  OPEN_API_GROUP: '开放接口分组'
}

export function dictTypeLabel(code) {
  return DICT_TYPE_LABEL[code] || code
}
'''
    io.open(E, 'w', encoding='utf-8').write(s)
    print('  ✓ enums.js 增加 DICT_TYPE_LABEL（16 类）')

# SysAdmin 改用 dictTypeLabel
P = r'D:\Work\业务平台开发\frontend\src\views\SysAdmin.vue'
t = io.open(P, encoding='utf-8').read()
t = t.replace(':label="enumLabel(null, t)"', ':label="dictTypeLabel(t)"')
t = t.replace("import { enumLabel } from '@/constants/enums'",
              "import { enumLabel, dictTypeLabel } from '@/constants/enums'")
io.open(P, 'w', encoding='utf-8').write(t)
print('  ✓ SysAdmin.vue 改用 dictTypeLabel')

m = re.search(r'<el-option[^>]*dictTypeLabel[^>]*>', t)
print('  → %s' % (m.group(0)[:96] if m else '未找到'))
