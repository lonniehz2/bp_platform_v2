# -*- coding: utf-8 -*-
"""房源台账页三项修复：
  2) 空间节点 → 可模糊搜索的下拉（树选择）
  3) 朝向 → 中文下拉
  5) 床位管理房间下拉为空 → 组织兜底
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'Houses.vue')
s = io.open(P, encoding='utf-8').read()

# ---------- 2) 空间节点：树选择 ----------
OLD_SPACE = """          <el-col :span="12"><el-form-item label="空间节点ID" required>
            <el-input v-model="f.spaceId" placeholder="房间级空间 ID" />
          </el-form-item></el-col>"""
NEW_SPACE = """          <el-col :span="12"><el-form-item label="空间节点" required>
            <el-tree-select v-model="f.spaceId" :data="spaceTree" check-strictly
                            filterable :render-after-expand="false"
                            :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                            placeholder="输入房间名搜索，如 1101室" style="width:100%"
                            @change="onSpacePicked" />
          </el-form-item></el-col>"""
if OLD_SPACE in s and 'onSpacePicked' not in s:
    s = s.replace(OLD_SPACE, NEW_SPACE, 1)

# ---------- 3) 朝向：中文下拉 ----------
OLD_ORI = """          <el-col :span="12"><el-form-item label="朝向">
            <el-input v-model="f.orientation" /></el-form-item></el-col>"""
NEW_ORI = """          <el-col :span="12"><el-form-item label="朝向">
            <el-select v-model="f.orientation" clearable style="width:100%"
                       placeholder="请选择朝向">
              <el-option v-for="o in ORIENTATIONS" :key="o.value" :label="o.label"
                         :value="o.value" />
            </el-select></el-form-item></el-col>"""
if OLD_ORI in s:
    s = s.replace(OLD_ORI, NEW_ORI, 1)

# ---------- 5) 床位房间下拉：组织兜底 ----------
OLD_OPEN = """async function openBeds() {
  bedVisible.value = true
  bedRows.value = []
  bedRoomId.value = ''
  if (!spaceTree.value.length) {
    try {
      const orgId = query.orgId || auth.user?.orgId
      const tree = await req.get('/spaces/tree', { params: { orgId } })
      spaceTree.value = tree || []
    } catch (e) { /* 忽略，用户可手动输入房间 ID */ }
  }
}"""
NEW_OPEN = """async function openBeds() {
  bedVisible.value = true
  bedRows.value = []
  bedRoomId.value = ''
  await ensureSpaceTree()
}

/**
 * 确保空间树可用。
 * 后端 /spaces/tree 必须带 orgId；账号无 orgId 时回退到第一个可选组织，
 * 否则房间下拉会是空白（本次修复点）。
 */
async function ensureSpaceTree() {
  if (spaceTree.value.length) return spaceTree.value
  let orgId = query.orgId || auth.user?.orgId
  if (!orgId) {
    try {
      const list = await req.get('/orgs/children')
      const first = (list || [])[0]
      orgId = first && first.id
    } catch (e) { /* 忽略 */ }
  }
  if (!orgId) return []
  try {
    const tree = await req.get('/spaces/tree', { params: { orgId } })
    spaceTree.value = tree || []
  } catch (e) {
    ElMessage.error('空间树加载失败：' + (e?.response?.data?.message || e?.message || e))
  }
  return spaceTree.value
}

/** 选中房间后自动带出组织/房号，减少手填 */
function onSpacePicked(id) {
  const hit = findNode(spaceTree.value, id)
  if (!hit) return
  if (!f.houseName) f.houseName = hit.spaceName
  if (!f.houseCode) f.houseCode = hit.spaceCode
  if (!f.orgId && hit.orgId) f.orgId = hit.orgId
  if (!f.area && hit.area) f.area = Number(hit.area)
}

function findNode(nodes, id) {
  for (const n of nodes || []) {
    if (String(n.id) === String(id)) return n
    const sub = findNode(n.children, id)
    if (sub) return sub
  }
  return null
}"""
if OLD_OPEN in s:
    s = s.replace(OLD_OPEN, NEW_OPEN, 1)

# 打开「新增房源」时预加载空间树
OLD_CREATE = """function openCreate() {"""
if OLD_CREATE in s and 'ensureSpaceTree()' not in s.split('function openCreate()')[1][:200]:
    s = s.replace("""function openCreate() {""",
                  """async function openCreate() {
  ensureSpaceTree()""", 1)

# 朝向常量
if 'ORIENTATIONS' not in s:
    s = s.replace("""const spaceTree = ref([])""",
                  """const spaceTree = ref([])

/** 朝向：与后端枚举一致（EnumLabels 已配中文） */
const ORIENTATIONS = [
  { value: 'SOUTH', label: '朝南' },
  { value: 'NORTH', label: '朝北' },
  { value: 'EAST', label: '朝东' },
  { value: 'WEST', label: '朝西' },
  { value: 'SOUTHEAST', label: '东南' },
  { value: 'SOUTHWEST', label: '西南' },
  { value: 'NORTHEAST', label: '东北' },
  { value: 'NORTHWEST', label: '西北' },
  { value: 'NORTH_SOUTH', label: '南北通透' }
]""", 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Houses.vue 已修：空间树选择 / 朝向中文 / 床位房间兜底')
