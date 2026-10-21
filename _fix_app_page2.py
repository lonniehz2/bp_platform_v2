# -*- coding: utf-8 -*-
"""补齐 currentNode 列与详情抽屉里的枚举显示"""
import io

A = r'D:\Work\业务平台开发\frontend\src\views\Applications.vue'
s = io.open(A, encoding='utf-8').read()

# 1) currentNode 列（后缀不在通用规则里，单独处理）
old = '<el-table-column prop="currentNode" label="当前环节" width="100" />'
new = ('<el-table-column prop="currentNode" label="当前环节" width="100">\n'
       '        <template #default="{ row }">'
       "{{ enumLabel('currentNode', row.currentNode) }}</template>\n"
       '      </el-table-column>')
if old in s:
    s = s.replace(old, new, 1)
    print('  ✓ currentNode 列改为中文')

# 2) 详情抽屉里的保障类型
old2 = '<el-descriptions-item label="保障类型">{{ current?.securityType }}</el-descriptions-item>'
new2 = ('<el-descriptions-item label="保障类型">'
        "{{ enumLabel('securityType', current?.securityType) }}</el-descriptions-item>")
if old2 in s:
    s = s.replace(old2, new2, 1)
    print('  ✓ 详情抽屉保障类型改为中文')

# 3) 详情里申请人
if 'label="申请人">' in s and 'personName' not in s.split('label="申请人">')[1][:40]:
    s = s.replace('<el-descriptions-item label="申请人">',
                  '<el-descriptions-item label="申请人">', 1)

io.open(A, 'w', encoding='utf-8').write(s)
print('  ✓ 保存')
