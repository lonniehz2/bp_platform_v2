# -*- coding: utf-8 -*-
"""修复展开/收起：改为操作 el-tree 的节点状态（default-expand-all 不响应式）"""
import io

P = r'D:\Work\业务平台开发\frontend\src\views\Spaces.vue'
s = io.open(P, encoding='utf-8').read()

# 1) 按钮改为调用真实函数
old_btn = '''      <el-button @click="expandAll = !expandAll">{{ expandAll ? '收起' : '展开' }}</el-button>'''
new_btn = '''      <el-button @click="toggleExpand">{{ expandAll ? '全部收起' : '全部展开' }}</el-button>
      <el-button @click="load">刷新</el-button>'''
if old_btn in s:
    s = s.replace(old_btn, new_btn, 1)
    print('  ✓ 按钮改为 toggleExpand')

# 2) 树：去掉 default-expand-all 的响应式误用，改为初始 true + key 重挂载兜底
s = s.replace('node-key="id" :default-expand-all="expandAll" highlight-current',
              'node-key="id" :key="treeKey" default-expand-all highlight-current')
print('  ✓ el-tree 改用 :key 强制重挂载')

# 3) 脚本：实现 toggleExpand
old_state = 'const expandAll = ref(true)'
new_state = 'const expandAll = ref(true)\nconst treeKey = ref(0)'
if old_state in s:
    s = s.replace(old_state, new_state, 1)

FUNC = '''
/**
 * 展开/收起。
 *
 * 注意：el-tree 的 default-expand-all 只在首次渲染生效，
 * 改这个 prop 不会更新已展开的节点（Element Plus 行为），
 * 因此这里直接操作内部节点状态，并用 treeKey 兜底重挂载。
 */
function toggleExpand() {
  expandAll.value = !expandAll.value
  const store = treeRef.value && treeRef.value.store
  if (store && store.nodesMap) {
    Object.values(store.nodesMap).forEach((node) => {
      node.expanded = expandAll.value
    })
  } else {
    // 树重建：让 default-expand-all 重新生效
    treeKey.value += 1
  }
}
'''

if 'function toggleExpand' not in s:
    s = s.replace('function onSelect(data) { current.value = data }',
                  FUNC + '\nfunction onSelect(data) { current.value = data }', 1)
    print('  ✓ 实现 toggleExpand（节点状态 + key 兜底）')

# 4) 加载后按当前展开状态同步一次（避免刷新后状态错乱）
s = s.replace('''    const d = await spaceApi.tree({ orgId: orgId.value })
    tree.value = Array.isArray(d) ? d : (d?.rows || [])''',
              '''    const d = await spaceApi.tree({ orgId: orgId.value })
    tree.value = Array.isArray(d) ? d : (d?.rows || [])
    // 数据变化后按当前展开偏好同步（nextTick 等树渲染完成）
    setTimeout(() => {
      const store = treeRef.value && treeRef.value.store
      if (store && store.nodesMap) {
        Object.values(store.nodesMap).forEach((n) => { n.expanded = expandAll.value })
      }
    }, 0)''', 1)

io.open(P, 'w', encoding='utf-8').write(s)

print('\n  校验：')
for kw in ('toggleExpand', 'treeKey', 'default-expand-all', 'nodesMap'):
    print('    %-22s %s' % (kw, '✓' if kw in s else '✗'))
