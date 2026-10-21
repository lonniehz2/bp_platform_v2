# -*- coding: utf-8 -*-
"""人员/房源加「改状态」、工单加全流程动作"""
import io

V = r'D:\Work\业务平台开发\frontend\src\views'
req = "import req from '@/api/request'"


def patch(file, ops_marker='<!--OPS-->'):
    p = V + '\\' + file
    s = io.open(p, encoding='utf-8').read()
    return p, s


# ---------- 人员：改状态 ----------
p, s = patch('Persons.vue')
if 'changeStatus' not in s:
    # 操作列 / 表格后追加按钮
    if 'label="操作"' in s:
        s = s.replace('''      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>''',
                      '''      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="changeStatus(row)">改状态</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>''', 1)
    # script 注入
    s = s.replace("import { personsApi }", "import { personsApi }", 1)
    if 'ElMessage' not in s:
        s = s.replace("import { ref, onMounted }", "import { ref, onMounted }", 1)
    s = s.replace('onMounted(load)', '''async function changeStatus(row) {
  const { value } = await ElMessageBox.prompt('输入新状态（NORMAL/FROZEN/CANCELLED）',
    '变更人员状态', { inputValue: row.personStatus || row.status || '' })
  await req.post(`/persons/${row.id}/status`, { status: value })
  ElMessage.success('已更新'); load()
}

onMounted(load)''', 1)
    # 补 import
    if 'ElMessageBox' not in s.split('</script>')[0]:
        s = s.replace("<script setup>\n", "<script setup>\n", 1)
        first_import = s.find('import ')
        s = s[:first_import] + ("import { ElMessage, ElMessageBox } from 'element-plus'\n"
                                "import req from '@/api/request'\n") + s[first_import:]
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ Persons.vue 加「改状态」')

# ---------- 房源：改状态 ----------
p, s = patch('Houses.vue')
if 'changeStatus' not in s:
    if 'label="操作"' in s:
        s = re.sub(r'(<el-table-column label="操作"[^>]*>\s*<template #default="\{ row \}">)',
                   r'\1\n          <el-button link type="primary" @click="changeStatus(row)">'
                   r'改状态</el-button>', s, count=1) if 're' in dir() else s
    if 'changeStatus' not in s:
        # 简单追加：在操作列前插入一列
        s = s.replace('      <el-table-column label="操作"',
                      '''      <el-table-column label="操作"''', 1)
    s = s.replace('onMounted(load)', '''async function changeStatus(row) {
  const { value } = await ElMessageBox.prompt(
    '输入新状态（VACANT/OCCUPIED/LOCKED/REPAIR/OFFLINE）', '变更房源状态',
    { inputValue: row.houseStatus || '' })
  await req.post(`/houses/${row.id}/status`, { status: value })
  ElMessage.success('已更新'); load()
}

onMounted(load)''', 1)
    if 'ElMessageBox' not in s.split('</script>')[0]:
        first_import = s.find('import ')
        s = s[:first_import] + ("import { ElMessage, ElMessageBox } from 'element-plus'\n"
                                "import req from '@/api/request'\n") + s[first_import:]
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ Houses.vue 加「改状态」函数（按钮需手工确认）')
