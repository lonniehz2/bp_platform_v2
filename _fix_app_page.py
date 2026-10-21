# -*- coding: utf-8 -*-
"""申请页：申请人显示姓名；补 ReviewStage 阶段中文"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 阶段枚举补充 ----------
E = os.path.join(FE, 'constants', 'enums.js')
s = io.open(E, encoding='utf-8').read()
if 'ACCEPT: ' not in s:
    s = s.replace("""  // ---------- 审批 / 流程 ----------""",
                  """  // ---------- 审批环节（ReviewStage）----------
  ACCEPT: '受理',
  FORM: '形式审核',
  JOINT: '联合审核',
  FINAL: '终审',
  DONE: '已完成',

  // ---------- 审批 / 流程 ----------""")
    io.open(E, 'w', encoding='utf-8').write(s)
    print('  ✓ enums.js 补 ReviewStage：ACCEPT/FORM/JOINT/FINAL/DONE')

# 阶段字段的覆盖（currentNode 用 ReviewStage）
if 'currentNode:' not in s:
    s = io.open(E, encoding='utf-8').read()
    s = s.replace("const TYPE_OVERRIDE = {",
                  "const TYPE_OVERRIDE = {\n"
                  "  currentNode: { ACCEPT: '受理', FORM: '形式审核', JOINT: '联合审核',\n"
                  "                  FINAL: '终审', DONE: '已完成' },")
    io.open(E, 'w', encoding='utf-8').write(s)
    print('  ✓ enums.js 补 currentNode 覆盖')

# ---------- 2) 申请页：personId → personName ----------
A = os.path.join(FE, 'views', 'Applications.vue')
a = io.open(A, encoding='utf-8').read()
if 'prop="personId" label="申请人"' in a:
    a = a.replace('<el-table-column prop="personId" label="申请人" width="110" />',
                  '<el-table-column prop="personName" label="申请人" width="110">\n'
                  '        <template #default="{ row }">\n'
                  '          {{ row.personName || row.personId }}\n'
                  '        </template>\n'
                  '      </el-table-column>', 1)
    io.open(A, 'w', encoding='utf-8').write(a)
    print('  ✓ Applications.vue：申请人显示 personName（回退 personId）')
else:
    print('  - Applications.vue 已处理或列定义不同')

# 打印当前申请页列
print('\n当前申请页列：')
for ln in io.open(A, encoding='utf-8').read().split('\n'):
    if 'el-table-column' in ln and ('label=' in ln):
        print('  ' + ln.strip()[:100])
