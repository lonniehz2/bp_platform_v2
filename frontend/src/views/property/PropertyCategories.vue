<template>
  <div class="category-page">
    <el-card shadow="never">
      <div class="toolbar">
        <el-radio-group v-model="type" @change="onTypeChange">
          <el-radio-button label="INCOME">{{ t('property.income') }}</el-radio-button>
          <el-radio-button label="EXPENSE">{{ t('property.expense') }}</el-radio-button>
        </el-radio-group>
        <div class="spacer" />
        <el-button type="primary" @click="openAdd(null)">{{ t('property.addCategory') }}</el-button>
      </div>

      <el-alert type="info" :closable="false" show-icon :title="t('property.categoryHint')"
                style="margin: 10px 0" />

      <el-table :data="tree" row-key="id" border size="small" v-loading="loading"
                :tree-props="{ children: 'children' }" default-expand-all>
        <el-table-column prop="categoryName" :label="t('property.categoryName')" min-width="220">
          <template #default="{ row }">
            <span>{{ row.categoryName }}</span>
            <el-tag v-if="row.isSystem === 1" size="small" type="info" style="margin-left:6px">
              {{ t('property.system') }}
            </el-tag>
            <el-tag v-if="row.allowCustom === 1" size="small" type="success" style="margin-left:6px">
              {{ t('property.extensible') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="categoryCode" :label="t('property.categoryCode')" width="220" />
        <el-table-column prop="reportLineCode" :label="t('property.reportLine')" width="160" />
        <el-table-column prop="sortNo" :label="t('property.sortNo')" width="80" />
        <el-table-column :label="t('property.status')" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
              {{ row.status === 'ENABLED' ? t('property.enabled') : t('property.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('property.actions')" width="300" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.allowCustom === 1" link type="primary" @click="openAdd(row)">
              {{ t('property.addChild') }}
            </el-button>
            <el-button link type="primary" @click="openEdit(row)">{{ t('property.edit') }}</el-button>
            <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                       @click="toggleStatus(row)">
              {{ row.status === 'ENABLED' ? t('property.disable') : t('property.enable') }}
            </el-button>
            <el-button v-if="row.isSystem !== 1" link type="danger" @click="remove(row)">
              {{ t('property.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? t('property.editCategory') : t('property.addCategory')"
               width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item :label="t('property.parentCategory')" required>
          <el-select v-model="form.parentId" style="width:100%" :disabled="!!form.id">
            <el-option v-for="p in rootOptions" :key="p.id" :label="p.categoryName" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('property.categoryCode')" required>
          <el-input v-model="form.categoryCode" :disabled="!!form.id"
                    :placeholder="t('property.codeHint')" />
        </el-form-item>
        <el-form-item :label="t('property.categoryName')" required>
          <el-input v-model="form.categoryName" />
        </el-form-item>
        <el-form-item :label="t('property.sortNo')">
          <el-input-number v-model="form.sortNo" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item :label="t('property.remark')">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('property.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ t('property.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const type = ref(route.query.tab === 'expense' ? 'EXPENSE' : 'INCOME')
const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const form = reactive({
  id: null, parentId: null, categoryCode: '', categoryName: '', sortNo: 0, remark: ''
})

const tree = computed(() => {
  const map = new Map()
  rows.value.forEach((r) => map.set(r.id, { ...r, children: [] }))
  const roots = []
  map.forEach((n) => {
    if (n.parentId && map.has(n.parentId)) map.get(n.parentId).children.push(n)
    else roots.push(n)
  })
  return roots
})

const rootOptions = computed(() => rows.value.filter((r) => !r.parentId && r.allowCustom === 1))

async function load() {
  loading.value = true
  try {
    rows.value = await req.get('/property/categories', { params: { type: type.value } }) || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('property.loadFailed'))
  } finally { loading.value = false }
}

function onTypeChange() {
  router.replace({ path: '/property/categories', query: { tab: type.value === 'EXPENSE' ? 'expense' : 'income' } })
  load()
}

function openAdd(parent) {
  form.id = null
  form.parentId = parent?.id || rootOptions.value[0]?.id || null
  form.categoryCode = ''
  form.categoryName = ''
  form.sortNo = 0
  form.remark = ''
  dialogVisible.value = true
}

function openEdit(row) {
  form.id = row.id
  form.parentId = row.parentId
  form.categoryCode = row.categoryCode
  form.categoryName = row.categoryName
  form.sortNo = row.sortNo
  form.remark = row.remark
  dialogVisible.value = true
}

async function save() {
  if (!form.parentId || !form.categoryCode.trim() || !form.categoryName.trim()) {
    ElMessage.warning(t('property.requiredHint'))
    return
  }
  saving.value = true
  try {
    if (form.id) {
      await req.put(`/property/categories/${form.id}`, {
        categoryName: form.categoryName, sortNo: form.sortNo, remark: form.remark
      })
    } else {
      await req.post('/property/categories', {
        categoryType: type.value, parentId: form.parentId,
        categoryCode: form.categoryCode, categoryName: form.categoryName,
        sortNo: form.sortNo, remark: form.remark
      })
    }
    ElMessage.success(t('property.saved'))
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('property.saveFailed'))
  } finally { saving.value = false }
}

async function toggleStatus(row) {
  try {
    await req.put(`/property/categories/${row.id}`, {
      status: row.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
    })
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('property.saveFailed'))
  }
}

async function remove(row) {
  await ElMessageBox.confirm(t('property.deleteConfirm', { name: row.categoryName }),
    t('property.delete'), { type: 'warning' })
  try {
    await req.delete(`/property/categories/${row.id}`)
    ElMessage.success(t('property.deleted'))
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('property.deleteFailed'))
  }
}

onMounted(load)
</script>

<style scoped>
.category-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: center; gap: 10px; }
.spacer { flex: 1; }
</style>
