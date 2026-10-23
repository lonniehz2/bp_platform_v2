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
          <el-tree :data="tree" :props="{ label: 'orgName', children: 'children' }"
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
          <el-input v-model="f.community" placeholder="社区、村委会名称（可手填）" /></el-form-item>
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
</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { orgApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import req from '@/api/request'

const loading = ref(false)
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
        value: r.code, label: r.name, leaf: r.leaf
      })))
    } catch (e) {
      resolve([])
    }
  }
}

function onRegionChange(codes) {
  if (!codes || !codes.length) {
    f.province = ''; f.city = ''; f.district = ''; f.street = ''
    return
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
  } finally {
    loading.value = false
  }
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
