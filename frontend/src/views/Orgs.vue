<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">组织机构</h3>
        <div class="spacer" />
        <el-radio-group v-model="viewMode" size="small" @change="load">
          <el-radio-button value="tree">树形</el-radio-button>
          <el-radio-button value="table">列表</el-radio-button>
        </el-radio-group>
        <el-checkbox v-model="includeSubtree" @change="onSubtreeChange">
          含下级
        </el-checkbox>
        <el-button type="primary" @click="load">刷新</el-button>
        <el-button type="success" @click="openCreate">新增组织</el-button>
      </div>

      <el-alert v-if="currentOrg" type="info" :closable="true" show-icon
                :title="`当前筛选：${currentOrg.orgName}（${includeSubtree ? '含所有下级' : '仅直接下级'}）`"
                style="margin-bottom:10px" @close="clearFilter" />

      <el-row :gutter="16">
        <el-col :span="7">
          <el-tree :data="tree" :props="{ label: 'treeLabel', children: 'children' }"
                   node-key="id" default-expand-all highlight-current
                   @node-click="onSelect" />
          <el-empty v-if="!tree.length" description="暂无组织数据" :image-size="60" />
        </el-col>
        <el-col :span="17">
          <el-table :data="rows" v-loading="loading" border size="small"
                     empty-text="该组织下暂无子组织（可勾选「含下级」查看全部）">
            <el-table-column prop="id" label="ID" width="150" />
            <el-table-column prop="orgName" label="组织名称" min-width="160" />
            <el-table-column prop="orgCode" label="编码" width="140" />
            <el-table-column prop="orgType" label="类型" width="110">
              <template #default="{ row }">
                {{ row.orgTypeLabel || enumLabel('orgType', row.orgType) }}
              

</template>
            </el-table-column>
            <el-table-column prop="parentId" label="上级" width="150">
              <template #default="{ row }">{{ row.parentIdName || row.parentId }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                  {{ row.statusLabel || enumLabel('status', row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDetail(row)">详情</el-button>
                <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                           @click="toggleStatus(row)">
                  {{ row.status === 'ENABLED' ? '停用' : '启用' }}
                </el-button>
                <el-button link type="danger" @click="removeOrg(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                         :total="total" :page-size="query.pageSize"
                         :current-page="query.pageNum"
                         @current-change="(p) => { query.pageNum = p; load() }" />
        </el-col>
      </el-row>
    </div>
  </div>

    <el-dialog v-model="createVisible" title="新增组织" width="560px">
      <el-form :model="f" label-width="110px">
        <el-form-item label="组织编码" required>
          <el-input v-model="f.orgCode" /></el-form-item>
        <el-form-item label="组织名称" required>
          <el-input v-model="f.orgName" /></el-form-item>
        <el-form-item label="上级组织">
          <el-input v-model="f.parentId"
                    placeholder="留空=顶级；填写则作为下级" /></el-form-item>
        <el-form-item label="组织类型" required>
          <el-select v-model="f.orgType" style="width:100%">
            <el-option label="区级 DISTRICT" value="DISTRICT" />
            <el-option label="社区/小区 COMMUNITY" value="COMMUNITY" />
            <el-option label="公司 COMPANY" value="COMPANY" />
            <el-option label="部门 DEPARTMENT" value="DEPARTMENT" />
          </el-select></el-form-item>
        <el-form-item label="标准地址">
          <el-cascader v-model="regionPath" :props="regionProps" clearable filterable
                       placeholder="省 / 地市 / 区县 / 街道乡镇（点击逐级选择）"
                       style="width:100%" @change="onRegionChange" />
          <div class="muted" style="font-size:12px;margin-top:4px">
            数据来源：国家统计局五级行政区划（已载入省/市/区县/街道共
            {{ regionCount }} 条）
          </div>
        </el-form-item>
        <el-form-item label="社区/村">
          <el-select v-model="f.community" filterable allow-create default-first-option
                     clearable placeholder="可从下拉选择，也可直接输入新社区名"
                     style="width:100%">
            <el-option v-for="c in communityOptions" :key="c" :label="c" :value="c" />
          </el-select>
          <div class="muted" style="font-size:12px;margin-top:4px">
            区划库为省/市/区县/街道四级；社区/村请从下拉选择已录入社区，或直接输入新名称
          </div>
        </el-form-item>
        <el-form-item label="详细地址">
          <el-input v-model="f.address"
                    placeholder="路牌、楼宇、房号等（如：天府三街199号3栋1单元1201）" /></el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="f.sortNo" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="f.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="detailVisible" title="组织详情" width="680px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="组织名称">{{ detailRow.orgName }}</el-descriptions-item>
        <el-descriptions-item label="编码">{{ detailRow.orgCode }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ enumLabel('orgType', detailRow.orgType) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ enumLabel('status', detailRow.status) }}</el-descriptions-item>
        <el-descriptions-item label="标准地址" :span="2">
          {{ standardAddress(detailRow) }}
        </el-descriptions-item>
        <el-descriptions-item label="社区/村">{{ detailRow.community || '—' }}</el-descriptions-item>
        <el-descriptions-item label="详细地址">{{ detailRow.address || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑组织" width="640px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="组织名称" required><el-input v-model="editForm.orgName" /></el-form-item>
        <el-form-item label="编码" required><el-input v-model="editForm.orgCode" /></el-form-item>
        <el-form-item label="标准地址">
          <div v-if="editAddrText" class="muted" style="font-size:12px;margin-bottom:4px">
            当前：{{ editAddrText }}
          </div>
          <el-cascader v-model="editRegionPath" :props="regionProps" clearable filterable
                       placeholder="如需修改，请重新逐级选择"
                       style="width:100%" @change="onEditRegionChange" />
        </el-form-item>
        <el-form-item label="社区/村">
          <el-select v-model="editForm.community" filterable allow-create
                     default-first-option clearable
                     placeholder="可从下拉选择，也可直接输入" style="width:100%">
            <el-option v-for="c in communityOptions" :key="c" :label="c" :value="c" />
          </el-select>
          <div class="muted" style="font-size:12px;margin-top:4px">
            区划库到街道为止；社区/村可选已录入名称，也可直接输入
          </div>
        </el-form-item>
        <el-form-item label="详细地址"><el-input v-model="editForm.address" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="editForm.sortNo" :min="1" /></el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, computed, onMounted } from 'vue'
import { orgApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import req from '@/api/request'

const loading = ref(false)
let reloadingRoot = false
const tree = ref([])
const rows = ref([])
const total = ref(0)
const viewMode = ref('tree')
const createVisible = ref(false)
const saving = ref(false)
const f = reactive({ orgCode: '', orgName: '', parentId: null,
  orgType: 'COMMUNITY', province: '', city: '', district: '', street: '', community: '',
  address: '', sortNo: 1, remark: '' })
const query = reactive({ pageNum: 1, pageSize: 20 })

/** 五级行政区划级联（懒加载，逐级请求 /sys/regions/children） */
const regionPath = ref([])
const regionCount = ref('31 万+')
const regionProps = {
  lazy: true,
  value: 'code',
  label: 'name',
  async lazyLoad(node, resolve) {
    const parentCode = node.level === 0 ? '' : node.value
    try {
      const list = await req.get('/sys/regions/children', {
        params: parentCode ? { parentCode } : {}
      })
      resolve((list || []).map((r) => ({
        code: r.code, name: r.name, leaf: r.leaf
      })))
    } catch (e) {
      resolve([])
    }
  }
}


/** 社区选项：优先取区划库第五级，其次取已有组织里用过的社区名 */
const communityOptions = ref([])

async function loadCommunities(streetCode) {
  const set = new Set()
  try {
    const list = await req.get('/sys/regions/children', { params: { parentCode: streetCode } })
    ;(list || []).forEach((r) => r.name && set.add(r.name))
  } catch (e) { /* 区划库未收录第五级时忽略 */ }
  // 合并历史输入：优先同街道，其次全部（便于复用已录入社区名）
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    const all = d.rows || d || []
    const sameStreet = all.filter((o) => !streetCode || o.streetCode === streetCode)
    sameStreet.forEach((o) => o.community && set.add(o.community))
    if (!set.size) {
      all.forEach((o) => o.community && set.add(o.community))
    }
  } catch (e) { /* 忽略 */ }
  communityOptions.value = Array.from(set)
}

function onRegionChange(codes) {
  if (!codes || !codes.length) {
    f.province = ''; f.city = ''; f.district = ''; f.street = ''
    f.provinceCode = ''; f.cityCode = ''; f.districtCode = ''; f.streetCode = ''
    communityOptions.value = []
    return
  }
  // 代码逐级落到表单，供后端保存（第五级社区允许手填，故不存代码）
  f.provinceCode = codes[0] || ''
  f.cityCode = codes[1] || ''
  f.districtCode = codes[2] || ''
  f.streetCode = codes[3] || ''
  if (f.streetCode) {
    loadCommunities(f.streetCode)
  }
  // codes 是逐级代码，按顺序映射到 省/市/区县/街道
  req.get('/sys/regions/path', { params: { code: codes[codes.length - 1] } })
    .then((path) => {
      const names = (path || []).map((x) => x.name)
      f.province = names[0] || ''
      f.city = names[1] || ''
      f.district = names[2] || ''
      f.street = names[3] || ''
    })
    .catch(() => { /* 忽略，保留已填名称 */ })
}
const includeSubtree = ref(false)
const currentOrg = ref(null)

async function loadTree() {
  try {
    // 后端只提供 /orgs/children（按 parentId 取子节点），无整树接口；
    // 这里做**真正的递归**加载，深度上限 6 层，并防环。
    const MAX_DEPTH = 6
    const seen = new Set()

    async function childrenOf(parentId) {
      const res = await orgApi.children(parentId)
      return Array.isArray(res) ? res : (res?.rows || [])
    }

    async function build(list, depth) {
      const out = []
      for (const n of list) {
        if (seen.has(n.id)) continue      // 防环
        seen.add(n.id)
        const node = { ...n }
        // 树节点标签：名称 + 编码 + 状态（否则树只显示名称，与列表看不出差异）
        node.treeLabel = `${n.orgName}（${n.orgCode || '-'}）`
          + (n.status === 'DISABLED' ? ' ⏸停用' : '')
        if (depth < MAX_DEPTH) {
          try {
            const kids = await childrenOf(n.id)
            if (kids.length) node.children = await build(kids, depth + 1)
          } catch (e) { /* 单节点失败不影响整棵树 */ }
        }
        out.push(node)
      }
      return out
    }

    const roots = await childrenOf()
    tree.value = await build(roots, 1)
  } catch (e) { tree.value = [] }
}


async function load() {
  loading.value = true
  try {
    const data = await orgApi.page({
      ...query,
      parentId: currentOrg.value ? currentOrg.value.id : undefined,
      includeSubtree: currentOrg.value ? includeSubtree.value : undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
    // 选中的组织可能已被删除（或不属于当前租户）：自动回到根级，避免整页空白
    if (total.value === 0 && currentOrg.value && !reloadingRoot) {
      reloadingRoot = true
      currentOrg.value = null
      try { await load() } finally { reloadingRoot = false }
    }
  } finally {
    loading.value = false
  }
}


/** 详情 / 编辑 / 启停 / 删除 */
const detailVisible = ref(false)
const detailRow = ref({})
const editVisible = ref(false)
const editForm = reactive({ id: null, orgName: '', orgCode: '', orgType: '',
  parentId: null, community: '', address: '', sortNo: 1, remark: '',
  province: '', city: '', district: '', street: '',
  provinceCode: '', cityCode: '', districtCode: '', streetCode: '', communityCode: ''
})

function openDetail(row) {
  detailRow.value = row
  detailVisible.value = true
}

function openEdit(row) {
  Object.assign(editForm, {
    id: row.id, orgName: row.orgName, orgCode: row.orgCode,
    orgType: row.orgType, parentId: row.parentId,
    community: row.community, address: row.address,
    sortNo: row.sortNo || 1, remark: row.remark,
    province: row.province, city: row.city,
    district: row.district, street: row.street
  })
  // 优先用代码回显，缺失时退回名称（兼容历史数据）
  const codes = [row.provinceCode, row.cityCode, row.districtCode, row.streetCode]
  editRegionPath.value = codes.every(Boolean)
    ? codes
    : []
  if (row.streetCode) {
    loadCommunities(row.streetCode)
  }
  editVisible.value = true
}

async function saveEdit() {
  try {
    await req.put(`/orgs/${editForm.id}`, { ...editForm })
    ElMessage.success('已保存')
    editVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  }
}

async function toggleStatus(row) {
  const next = row.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.post(`/orgs/${row.id}/status`, { status: next })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

async function removeOrg(row) {
  try {
    await ElMessageBox.confirm(`确认删除组织「${row.orgName}」？`, '提示', { type: 'warning' })
    await req.delete(`/orgs/${row.id}`)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.message || '删除失败')
  }
}


/** 标准地址：省市区街道拼接 */
function standardAddress(row) {
  const parts = [row.province, row.city, row.district, row.street].filter(Boolean)
  return parts.length ? parts.join(' / ') : '—'
}

/** 当前标准地址文字（级联懒加载无法回显标签时用名称展示） */
const editAddrText = computed(() => {
  const parts = [editForm.province, editForm.city, editForm.district, editForm.street]
    .filter(Boolean)
  const code = editForm.provinceCode ? '（已存代码）' : ''
  return parts.length ? parts.join(' / ') + code : ''
})

/** 编辑弹窗内的标准地址级联 */
const editRegionPath = ref([])

function onEditRegionChange(codes) {
  if (!codes || !codes.length) {
    editForm.province = ''; editForm.city = ''
    editForm.district = ''; editForm.street = ''
    editForm.provinceCode = ''; editForm.cityCode = ''
    editForm.districtCode = ''; editForm.streetCode = ''
    return
  }
  editForm.provinceCode = codes[0] || ''
  editForm.cityCode = codes[1] || ''
  editForm.districtCode = codes[2] || ''
  editForm.streetCode = codes[3] || ''
  if (editForm.streetCode) {
    loadCommunities(editForm.streetCode)
  }
  req.get('/sys/regions/path', { params: { code: codes[codes.length - 1] } })
    .then((path) => {
      const names = (path || []).map((x) => x.name)
      editForm.province = names[0] || ''
      editForm.city = names[1] || ''
      editForm.district = names[2] || ''
      editForm.street = names[3] || ''
    })
    .catch(() => {})
}

function openCreate() {
  Object.assign(f, { orgCode: '', orgName: '',
    parentId: currentOrg.value ? currentOrg.value.id : null,
    orgType: 'COMMUNITY', province: '', city: '', district: '', street: '',
    community: '', address: '', sortNo: 1, remark: '' })
  createVisible.value = true
}

async function doCreate() {
  if (!f.orgCode || !f.orgName) {
    ElMessage.warning('组织编码与名称为必填'); return
  }
  saving.value = true
  try {
    await req.post('/orgs', { ...f })
    ElMessage.success('组织已创建')
    createVisible.value = false
    loadTree(); load()
  } finally { saving.value = false }
}

function onSelect(node) {
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
}

onMounted(async () => { await loadTree(); await load() })
</script>
