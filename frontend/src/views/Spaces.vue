<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('space.title') }}</h3>
      <el-tag size="small" type="info">
        {{ t('spaceX.flow') }}
      </el-tag>
      <div class="spacer" />
      <el-select v-model="orgId" :placeholder="t('space.orgHint')"
                 filterable style="width:230px" @change="load">
        <el-option v-for="o in orgs" :key="o.id" :label="o.orgName" :value="o.id" />
      </el-select>
      <el-button type="primary" @click="load">{{ t('space.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('space.reset') }}</el-button>
      <el-button @click="toggleExpand">{{ expandAll ? t('space.collapse') : t('space.expand') }}</el-button>
      <el-button @click="load">{{ t('space.refresh') }}</el-button>
      <el-button type="success" @click="openCreate">{{ t('space.create') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="t('spaceX.treeTip')"
              style="margin-bottom:12px" />

    <el-row :gutter="14">
      <el-col :span="9">
        <el-tree ref="treeRef" :data="tree" :props="{ label: 'spaceName', children: 'children' }"
                 node-key="id" :key="treeKey" default-expand-all highlight-current
                 @node-click="onSelect">
          <template #default="{ data }">
            <span>
              {{ data.spaceName }}
              <el-tag size="small" type="info" style="margin-left:6px">
                {{ data.spaceTypeLabel || data.spaceType }}
              </el-tag>
            </span>
          </template>
        </el-tree>
        <el-empty v-if="!tree.length" :description="t('spaceX.noData')" :image-size="60" />
      </el-col>
      <el-col :span="15">
        <el-descriptions v-if="current" :column="2" border size="small"
                         :title="t('space.detail')">
          <el-descriptions-item :label="t('space.id')">{{ current.id }}</el-descriptions-item>
          <el-descriptions-item :label="t('space.name')">{{ current.spaceName }}</el-descriptions-item>
          <el-descriptions-item :label="t('space.code')">{{ current.spaceCode }}</el-descriptions-item>
          <el-descriptions-item :label="t('space.type')">{{ current.spaceTypeLabel || current.spaceType }}</el-descriptions-item>
          <el-descriptions-item :label="t('space.path')">{{ current.pathCode }}</el-descriptions-item>
          <el-descriptions-item :label="t('space.level')">{{ current.spaceLevel }}</el-descriptions-item>
          <el-descriptions-item :label="t('space.area')">{{ current.area || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="t('space.status')">{{ enumLabel('spaceStatus', current.status) || current.status }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else :description="t('spaceX.pickNode')" :image-size="60" />
        <div v-if="current" class="toolbar" style="margin:8px 0 12px">
          <el-button type="primary" plain @click="openEdit(current)">{{ t('space.edit') }}</el-button>
          <el-button type="danger" plain @click="removeSpace">{{ t('space.delete') }}</el-button>
          <el-button plain @click="openCreateChild">{{ t('space.addChild') }}</el-button>
        </div>
        <DetailView :row="detail || current || row || {}" />
      </el-col>
    </el-row>

    <el-dialog v-model="createVisible" :title="t('space.createTitle')" width="560px">
      <el-form :model="f" label-width="120px">
        <el-form-item :label="t('space.org')" required>
          <el-select v-model="f.orgId" filterable :placeholder="t('spaceX.orgHint')"
                     style="width:100%" @change="onOrgChange">
            <el-option v-for="o in orgs" :key="o.id" :label="o.orgName" :value="o.id" />
          </el-select></el-form-item>
        <el-form-item :label="t('space.parent')">
          <el-tree-select v-model="f.parentId" :data="tree" check-strictly clearable
                          filterable :render-after-expand="false"
                          :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                          :placeholder="t('space.parentHint')" style="width:100%"
                          @change="onParentChange" />
        </el-form-item>
        <el-form-item :label="t('space.codeLabel')" required
                      :error="codeDupMsg ? codeDupMsg : ''">
          <el-input v-model="f.spaceCode" :placeholder="t('spaceX.codeHint')"
                    @blur="checkCodeDup" @input="codeDupMsg = ''" />
          <div class="muted" style="font-size:12px;margin-top:4px">
            <template v-if="codePrefix">
              {{ t('spaceX.prefixPre') }} <b>{{ codePrefix }}</b>{{ t('spaceX.prefixHint2') }}
            </template>
            <template v-else>{{ t('spaceX.prefixElse') }}</template>
          </div>
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon style="margin-bottom:8px"
                   :title="t('spaceX.innerRoomTip')" />
        <el-form-item :label="t('spaceX.name')" required>
          <el-input v-model="f.spaceName" /></el-form-item>
        <el-form-item :label="t('spaceX.type')" required>
          <el-select v-model="f.spaceType" style="width:100%">
            <el-option :label="t('space.area')" value="AREA" />
            <el-option :label="t('space.building')" value="BUILDING" />
            <el-option :label="t('space.unit')" value="UNIT" />
            <el-option :label="t('space.floor')" value="FLOOR" />
            <el-option :label="t('space.room')" value="ROOM" />
            <el-option :label="t('space.bed')" value="BED" />
            <el-option :label="t('space.parking')" value="PARKING" />
            <el-option :label="t('space.garage')" value="GARAGE" />
            <el-option :label="t('space.site')" value="SITE" />
          </el-select></el-form-item>
        <el-form-item :label="t('spaceX.area')">
          <el-input-number v-model="f.area" :min="0" :precision="2"
                           style="width:100%" /></el-form-item>
        <el-form-item :label="t('spaceX.sort')">
          <el-input-number v-model="f.sortNo" :min="1" style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                :title="t('spaceX.hierarchyTip')" />
      <template #footer>
        <el-button @click="createVisible = false">{{ t('spaceX.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('spaceX.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" :title="t('spaceX.editTitle')" width="520px">
      <el-form :model="ef" label-width="110px">
        <el-form-item :label="t('spaceX.org')">
          <span>{{ editOrgName || '—' }}</span>
        </el-form-item>
        <el-form-item :label="t('spaceX.parent')">
          <span>{{ editParentName || t('spaceX.top') }}</span>
        </el-form-item>
        <el-form-item label="空间类型">
          <span>{{ enumLabel('spaceType', ef.spaceType) }}</span>
        </el-form-item>
        <el-form-item :label="t('spaceX.name')" required>
          <el-input v-model="ef.spaceName" />
        </el-form-item>
        <el-form-item :label="t('spaceX.code')" required>
          <el-input v-model="ef.spaceCode" />
        </el-form-item>
        <el-form-item label="面积(㎡)">
          <el-input-number v-model="ef.area" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="ef.sortNo" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('spaceX.status')">
          <el-select v-model="ef.status" style="width:100%">
            <el-option :label="t('spaceX.enable')" value="ENABLED" />
            <el-option :label="t('spaceX.disable')" value="DISABLED" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('spaceX.remark')">
          <el-input v-model="ef.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">{{ t('spaceX.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doEdit">{{ t('spaceX.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import DetailView from '@/components/DetailView.vue'
import { ref, reactive, onMounted } from 'vue'
import { spaceApi, orgApi } from '@/api/modules'
import { enumLabel } from '@/constants/enums'
import { ElMessage, ElMessageBox } from 'element-plus'

const { t } = useI18n()
const tree = ref([])
const current = ref(null)
const orgId = ref(null)
const expandAll = ref(true)
const treeKey = ref(0)
const orgs = ref([])
const treeRef = ref(null)
const editVisible = ref(false)
const editOrgName = ref('')
const editParentName = ref('')
const ef = reactive({ id: null, spaceName: '', spaceCode: '', area: null,
  sortNo: 1, status: 'ENABLED', remark: '', spaceType: '' })

function openEdit(node) {
  Object.assign(ef, {
    id: node.id, spaceName: node.spaceName, spaceCode: node.spaceCode,
    area: node.area ? Number(node.area) : null, sortNo: node.sortNo || 1,
    status: node.status || 'ENABLED', remark: node.remark || '',
    spaceType: node.spaceType
  })
  editOrgName.value = node.orgIdName
    || (orgs.value.find((o) => String(o.id) === String(node.orgId)) || {}).orgName || ''
  editParentName.value = findNode(tree.value, node.parentId)?.spaceName || ''
  editVisible.value = true
}

async function doEdit() {
  if (!ef.spaceName || !ef.spaceCode) {
    ElMessage.warning(t('spaceX.required')); return
  }
  saving.value = true
  try {
    await spaceApi.update(ef.id, {
      spaceName: ef.spaceName, spaceCode: ef.spaceCode, area: ef.area,
      sortNo: ef.sortNo, status: ef.status, remark: ef.remark
    })
    ElMessage.success(t('spaceX.saved'))
    editVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('spaceX.saveFailed'))
  } finally { saving.value = false }
}

/** 在当前节点下新增子节点 */
function openCreateChild() {
  openCreate()
  f.parentId = current.value ? current.value.id : null
}

/** 切换组织后刷新空间树，供上级节点下拉使用 */
async function onOrgChange(id) {
  if (!id) return
  orgId.value = id
  await load()
}

const createVisible = ref(false)
const saving = ref(false)
const f = reactive({ orgId: null, parentId: null, spaceCode: '',
  spaceName: '', spaceType: 'ROOM', area: null, sortNo: 1 })

function openCreate() {
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
  codeDupMsg.value = hit ? t('spaceX.codeDup', { code, name: hit.spaceName }) : ''
}

async function doCreate() {
  if (!f.orgId || !f.spaceCode || !f.spaceName) {
    ElMessage.warning(t('spaceX.orgRequired'))
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
    ElMessage.success(t('spaceX.created'))
    createVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('spaceX.createFailed'))
  } finally { saving.value = false }
}

async function removeSpace() {
  await ElMessageBox.confirm(
    t('spaceX.deleteConfirm', { name: current.value.spaceName }),
    t('spaceX.deleteTitle'), { type: 'warning' })
  await spaceApi.remove(current.value.id)
  ElMessage.success(t('spaceX.deleted'))
  current.value = null
  load()
}

function findNode(nodes, id, field, value) {
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
}

async function load() {
  // 后端 /spaces/tree 强制要求 orgId（缺参会返回 BP10002）
  if (!orgId.value) {
    ElMessage.warning(t('spaceX.orgHint'))
    tree.value = []
    return
  }
  try {
    const d = await spaceApi.tree({ orgId: orgId.value })
    tree.value = Array.isArray(d) ? d : (d?.rows || [])
    // 数据变化后按当前展开偏好同步（nextTick 等树渲染完成）
    setTimeout(() => {
      const store = treeRef.value && treeRef.value.store
      if (store && store.nodesMap) {
        Object.values(store.nodesMap).forEach((n) => { n.expanded = expandAll.value })
      }
    }, 0)
  } catch (e) {
    tree.value = []
    ElMessage.error(t('spaceX.loadFailed', { msg: e?.message || e }))
  }
}


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

function onSelect(data) { current.value = data }

/** 加载可选的根组织；默认选第一个并直接展示空间树 */
async function loadOrgs() {
  try {
    const d = await orgApi.children()
    orgs.value = Array.isArray(d) ? d : (d.rows || [])
    if (!orgId.value && orgs.value.length) {
      // 优先选名称含「演示」的组织，便于验收
      const demo = orgs.value.find((o) => (o.orgName || '').includes('演示'))
      orgId.value = (demo || orgs.value[0]).id
    }
    if (orgId.value) await load()
  } catch (e) {
    orgs.value = []
    ElMessage.error(t('spaceX.orgLoadFailed', { msg: e?.message || e }))
  }
}

function resetQuery() {
  orgId.value = ''
  load()
}

onMounted(loadOrgs)
</script>

<style scoped>
.raw { max-height: 260px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; margin-top: 12px;
  white-space: pre-wrap; }
</style>
