# -*- coding: utf-8 -*-
"""Orgs.vue：选中节点过滤右侧 + 含下级开关 + 当前范围提示"""
import io

P = r'D:\Work\业务平台开发\frontend\src\views\Orgs.vue'
s = io.open(P, encoding='utf-8').read()

# 1) 工具栏加「含下级」开关 + 当前筛选提示
old_tool = '''        <el-button type="primary" @click="load">刷新</el-button>
      </div>'''
new_tool = '''        <el-checkbox v-model="includeSubtree" @change="onSubtreeChange">
          含下级
        </el-checkbox>
        <el-button type="primary" @click="load">刷新</el-button>
      </div>

      <el-alert v-if="currentOrg" type="info" :closable="true" show-icon
                :title="`当前筛选：${currentOrg.orgName}（${includeSubtree ? '含所有下级' : '仅直接下级'}）`"
                style="margin-bottom:10px" @close="clearFilter" />'''
assert old_tool in s
s = s.replace(old_tool, new_tool, 1)

# 2) 表格上方提示当前为空时的原因
s = s.replace('<el-table :data="rows" v-loading="loading" border size="small">',
              '''<el-table :data="rows" v-loading="loading" border size="small"
                     empty-text="该组织下暂无子组织（可勾选「含下级」查看全部）">''', 1)

# 3) 脚本：状态与处理函数
s = s.replace("const query = reactive({ pageNum: 1, pageSize: 20, parentId: undefined })",
              "const query = reactive({ pageNum: 1, pageSize: 20 })\n"
              "const includeSubtree = ref(false)\n"
              "const currentOrg = ref(null)", 1)

s = s.replace('''    const data = await orgApi.page({ ...query })''',
              '''    const data = await orgApi.page({
      ...query,
      parentId: currentOrg.value ? currentOrg.value.id : undefined,
      includeSubtree: currentOrg.value ? includeSubtree.value : undefined
    })''', 1)

s = s.replace('''function onSelect(node) {
  query.parentId = node.id
  query.pageNum = 1
  load()
}''',
              '''function onSelect(node) {
  currentOrg.value = node
  query.pageNum = 1
  load()
}

function onSubtreeChange() {
  if (currentOrg.value) {
    query.pageNum = 1
    load()
  }
}

function clearFilter() {
  currentOrg.value = null
  query.pageNum = 1
  load()
}''', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ Orgs.vue：选中节点过滤 + 含下级开关 + 范围提示')

# 校验
out = io.open(P, encoding='utf-8').read()
for kw in ('includeSubtree', 'currentOrg', 'onSubtreeChange', 'clearFilter',
           'empty-text'):
    print('   %-16s %s' % (kw, '✓' if kw in out else '✗'))
