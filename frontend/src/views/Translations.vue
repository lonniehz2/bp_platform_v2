<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('trans.title') }}</h3>
      <el-select v-model="resourceType" clearable style="width:160px" @change="load">
        <el-option v-for="t in TYPES" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <el-button type="primary" @click="load">{{ t('trans.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('trans.reset') }}</el-button>
      <div class="spacer" />
      <el-button type="success" @click="openCreate">{{ t('trans.add') }}</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('trans.empty')">
      <el-table-column prop="resource_type" :label="t('trans.type')" width="140" />
      <el-table-column prop="resource_id" :label="t('trans.resourceId')" width="190" />
      <el-table-column prop="field" :label="t('trans.field')" width="110" />
      <el-table-column prop="text" :label="t('trans.text')" min-width="220" />
      <el-table-column prop="status" :label="t('trans.status')" width="100" />
      <el-table-column :label="t('trans.actions')" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">{{ t('trans.edit') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" :title="t('trans.dialogTitle')" width="520px">
      <el-form label-width="110px">
        <el-form-item :label="t('trans.type')" required>
          <el-select v-model="form.resourceType" style="width:100%">
            <el-option v-for="t in TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('trans.resourceId')" required>
          <el-input v-model="form.resourceId" />
        </el-form-item>
        <el-form-item :label="t('trans.field')" required>
          <el-input v-model="form.field" />
        </el-form-item>
        <el-form-item :label="t('trans.text')" required>
          <el-input v-model="form.text" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('trans.status')">
          <el-select v-model="form.status" style="width:100%">
            <el-option :label="t('trans.enabled')" value="ENABLED" />
            <el-option :label="t('trans.disabled')" value="DISABLED" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">{{ t('trans.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ t('trans.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import req from '@/api/request'

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const resourceType = ref('')
const visible = ref(false)
const form = ref({ resourceType: 'org', resourceId: '', field: 'name', text: '', status: 'ENABLED' })

const TYPES = computed(() => [
  { value: 'org', label: t('trans.org') },
  { value: 'house', label: t('trans.house') },
  { value: 'person', label: t('trans.person') },
  { value: 'space', label: t('trans.space') },
  { value: 'fee_item', label: t('trans.feeItem') },
  { value: 'device', label: t('trans.device') }
])

async function load() {
  loading.value = true
  try {
    rows.value = await req.get('/i18n/texts', {
      params: { locale: 'en-US', resourceType: resourceType.value || undefined }
    }) || []
  } catch (e) {
    rows.value = []
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  resourceType.value = ''
  load()
}

function openCreate() {
  form.value = { resourceType: 'org', resourceId: '', field: 'name', text: '', status: 'ENABLED' }
  visible.value = true
}

function openEdit(row) {
  form.value = {
    resourceType: row.resource_type,
    resourceId: String(row.resource_id),
    field: row.field,
    text: row.text,
    status: row.status
  }
  visible.value = true
}

async function save() {
  if (!form.value.resourceId || !form.value.text) {
    ElMessage.warning(t('trans.empty'))
    return
  }
  saving.value = true
  try {
    await req.post('/i18n/texts', {
      ...form.value,
      locale: 'en-US'
    })
    visible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
