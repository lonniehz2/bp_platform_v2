# -*- coding: utf-8 -*-
"""新增空间：空间编码按「上级编码+分隔符」预填，并做重复校验。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'Spaces.vue')
s = io.open(P, encoding='utf-8').read()
n = 0

# 1) 上级节点：切换时同步前缀
OLD_PARENT = """          <el-tree-select v-model="f.parentId" :data="tree" check-strictly clearable
                          filterable :render-after-expand="false"
                          :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                          placeholder="留空=顶级（只能是楼栋/片区）" style="width:100%" />"""
NEW_PARENT = """          <el-tree-select v-model="f.parentId" :data="tree" check-strictly clearable
                          filterable :render-after-expand="false"
                          :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                          placeholder="留空=顶级（只能是楼栋/片区）" style="width:100%"
                          @change="onParentChange" />"""
if OLD_PARENT in s:
    s = s.replace(OLD_PARENT, NEW_PARENT, 1)
    n += 1

# 2) 空间编码：提示 + 失焦查重
OLD_CODE = """        <el-form-item label="空间编码" required>
          <el-input v-model="f.spaceCode" placeholder="同级唯一，建议用层级前缀" />
        </el-form-item>"""
NEW_CODE = """        <el-form-item label="空间编码" required
                      :error="codeDupMsg ? codeDupMsg : ''">
          <el-input v-model="f.spaceCode" placeholder="只需补当前层级编码"
                    @blur="checkCodeDup" @input="codeDupMsg = ''" />
          <div class="muted" style="font-size:12px;margin-top:4px">
            <template v-if="codePrefix">
              已按上级编码预填前缀 <b>{{ codePrefix }}</b>，只需在后面补本级编码（如 01）
            </template>
            <template v-else>建议格式：上级编码 + 分隔符 + 本级编码</template>
          </div>
        </el-form-item>"""
if OLD_CODE in s:
    s = s.replace(OLD_CODE, NEW_CODE, 1)
    n += 1

# 3) 打开新增时按上级/组织预填
OLD_OPEN = """function openCreate() {
  f.orgId = orgId.value
  f.parentId = current.value ? current.value.id : null
  createVisible.value = true
}"""
NEW_OPEN = """function openCreate() {
  f.orgId = orgId.value
  f.parentId = current.value ? current.value.id : null
  codeDupMsg.value = ''
  applyCodePrefix(true)
  createVisible.value = true
}

/** 空间编码前缀：上级空间编码 + '-'；顶级则用组织编码 + '-' */
const CODE_SEP = '-'
const codePrefix = ref('')
const codeDupMsg = ref('')

function prefixFor(parentId, orgIdValue) {
  if (parentId) {
    const p = findNode(tree.value, parentId)
    if (p && p.spaceCode) return p.spaceCode + CODE_SEP
    return ''
  }
  const org = orgs.value.find((o) => String(o.id) === String(orgIdValue || f.orgId))
  return org && org.orgCode ? org.orgCode + CODE_SEP : ''
}

/** 预填/更新前缀：保留用户已输入的后缀（切换上级时不丢已填内容） */
function applyCodePrefix(overwrite) {
  const next = prefixFor(f.parentId, f.orgId)
  if (overwrite || !f.spaceCode) {
    f.spaceCode = next
  } else if (codePrefix.value && f.spaceCode.startsWith(codePrefix.value)) {
    f.spaceCode = next + f.spaceCode.slice(codePrefix.value.length)
  } else if (next && !f.spaceCode.startsWith(next)) {
    f.spaceCode = next + f.spaceCode
  }
  codePrefix.value = next
  codeDupMsg.value = ''
}

function onParentChange() {
  applyCodePrefix(false)
}

/** 同级/全局编码查重（后端也会校验，这里提前提示） */
function checkCodeDup() {
  const code = (f.spaceCode || '').trim()
  if (!code) { codeDupMsg.value = ''; return }
  const hit = findNode(tree.value, null, 'spaceCode', code)
  codeDupMsg.value = hit ? ('编码已存在：' + code + '（' + hit.spaceName + '）') : ''
}"""
if OLD_OPEN in s:
    s = s.replace(OLD_OPEN, NEW_OPEN, 1)
    n += 1

# 4) findNode 支持按字段查（兼容原调用）
OLD_FIND = """function findNode(nodes, id) {
  if (!id) return null
  for (const n of nodes || []) {
    if (String(n.id) === String(id)) return n
    const sub = findNode(n.children, id)
    if (sub) return sub
  }
  return null
}"""
NEW_FIND = """function findNode(nodes, id, field, value) {
  if (field) {
    for (const n of nodes || []) {
      if (String(n[field]) === String(value)) return n
      const sub = findNode(n.children, null, field, value)
      if (sub) return sub
    }
    return null
  }
  if (!id) return null
  for (const n of nodes || []) {
    if (String(n.id) === String(id)) return n
    const sub = findNode(n.children, id)
    if (sub) return sub
  }
  return null
}"""
if OLD_FIND in s:
    s = s.replace(OLD_FIND, NEW_FIND, 1)
    n += 1

# 5) 提交前拦截 + 错误提示
OLD_DO = """async function doCreate() {
  if (!f.orgId || !f.spaceCode || !f.spaceName) {
    ElMessage.warning('组织ID、编码、名称为必填')
    return
  }
  saving.value = true
  try {
    await spaceApi.create({ ...f })
    ElMessage.success('空间已创建')
    createVisible.value = false
    load()
  } finally { saving.value = false }
}"""
NEW_DO = """async function doCreate() {
  if (!f.orgId || !f.spaceCode || !f.spaceName) {
    ElMessage.warning('组织、编码、名称为必填')
    return
  }
  checkCodeDup()
  if (codeDupMsg.value) {
    ElMessage.warning(codeDupMsg.value)
    return
  }
  saving.value = true
  try {
    await spaceApi.create({ ...f })
    ElMessage.success('空间已创建')
    createVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally { saving.value = false }
}"""
if OLD_DO in s:
    s = s.replace(OLD_DO, NEW_DO, 1)
    n += 1

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Spaces.vue 改动:', n, '/ 6')
