# -*- coding: utf-8 -*-
"""空间页：orgId 必填提示 + 错误处理"""
import io

P = r'D:\Work\业务平台开发\frontend\src\views\Spaces.vue'
s = io.open(P, encoding='utf-8').read()

s = s.replace("""import { ref, onMounted } from 'vue'
import { spaceApi } from '@/api/modules'""",
              """import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { spaceApi } from '@/api/modules'""", 1)

s = s.replace("""async function load() {
  try {
    const d = await spaceApi.tree({ orgId: orgId.value || undefined })
    tree.value = Array.isArray(d) ? d : (d?.rows || [])
  } catch (e) { tree.value = [] }
}""",
              """async function load() {
  // 后端 /spaces/tree 强制要求 orgId（缺参会返回 BP10002）
  if (!orgId.value) {
    ElMessage.warning('请输入组织ID后再查询（后端按组织返回空间树）')
    tree.value = []
    return
  }
  try {
    const d = await spaceApi.tree({ orgId: orgId.value })
    tree.value = Array.isArray(d) ? d : (d?.rows || [])
  } catch (e) { tree.value = [] }
}""", 1)

# 未填 orgId 时不自动查询
s = s.replace('onMounted(load)', 'onMounted(() => { /* 需先输入组织ID */ })', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ Spaces.vue：orgId 改为必填并加提示')
