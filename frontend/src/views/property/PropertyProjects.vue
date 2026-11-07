<template>
  <div class="project-page">
    <el-card shadow="never">
      <div class="toolbar">
        <div>
          <div class="page-title">{{ t('property.projects') }}</div>
          <div class="page-sub">{{ t('property.projectHint') }}</div>
        </div>
        <div class="spacer" />
        <el-button type="primary" @click="openCreate">{{ t('property.addProject') }}</el-button>
      </div>

      <el-table :data="store.projects" border size="small" v-loading="store.loading">
        <el-table-column prop="projectCode" :label="t('property.projectCode')" width="150" />
        <el-table-column prop="projectName" :label="t('property.projectName')" min-width="180" />
        <el-table-column prop="companyName" :label="t('property.companyName')" min-width="180" />
        <el-table-column prop="servicePhone" :label="t('property.servicePhone')" width="150" />
        <el-table-column prop="address" :label="t('property.address')" show-overflow-tooltip />
        <el-table-column :label="t('property.status')" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
              {{ row.status === 'ENABLED' ? t('property.enabled') : t('property.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('property.actions')" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">{{ t('property.edit') }}</el-button>
            <el-button link @click="choose(row)">{{ t('property.selectProject') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="visible" :title="form.orgId ? t('property.editProject') : t('property.addProject')"
               width="600px">
      <el-form :model="form" label-width="110px">
        <el-form-item :label="t('property.projectCode')" required>
          <el-input v-model="form.orgCode" :disabled="!!form.orgId" />
        </el-form-item>
        <el-form-item :label="t('property.projectName')" required>
          <el-input v-model="form.projectName" />
        </el-form-item>
        <el-form-item :label="t('property.companyName')">
          <el-input v-model="form.companyName" />
        </el-form-item>
        <el-form-item :label="t('property.contactName')">
          <el-input v-model="form.contactName" />
        </el-form-item>
        <el-form-item :label="t('property.contactPhone')">
          <el-input v-model="form.contactPhone" />
        </el-form-item>
        <el-form-item :label="t('property.servicePhone')">
          <el-input v-model="form.servicePhone" />
        </el-form-item>
        <el-form-item :label="t('property.address')">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item :label="t('property.receiptHeader')">
          <el-input v-model="form.receiptHeader" />
        </el-form-item>
        <el-form-item v-if="form.orgId" :label="t('property.status')">
          <el-select v-model="form.status" style="width:100%">
            <el-option :label="t('property.enabled')" value="ENABLED" />
            <el-option :label="t('property.disabled')" value="DISABLED" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">{{ t('property.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ t('property.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { usePropertyStore } from '@/store/property'

const { t } = useI18n()
const store = usePropertyStore()
const visible = ref(false)
const saving = ref(false)
const form = reactive({
  orgId: null, orgCode: '', projectName: '', companyName: '', contactName: '',
  contactPhone: '', servicePhone: '', address: '', receiptHeader: '', status: 'ENABLED'
})

onMounted(() => store.loadProjects())

function openCreate() {
  Object.assign(form, {
    orgId: null, orgCode: '', projectName: '', companyName: '', contactName: '',
    contactPhone: '', servicePhone: '', address: '', receiptHeader: '', status: 'ENABLED'
  })
  visible.value = true
}

function openEdit(row) {
  Object.assign(form, row, { orgId: row.orgId })
  visible.value = true
}

function choose(row) {
  store.selectProject(String(row.orgId))
  ElMessage.success(t('property.projectSelected', { name: row.projectName }))
}

async function save() {
  if (!form.projectName.trim() || (!form.orgId && !form.orgCode.trim())) {
    ElMessage.warning(t('property.projectRequired'))
    return
  }
  saving.value = true
  try {
    if (form.orgId) {
      await req.put(`/property/projects/${form.orgId}`, {
        projectName: form.projectName, companyName: form.companyName,
        contactName: form.contactName, contactPhone: form.contactPhone,
        servicePhone: form.servicePhone, address: form.address,
        receiptHeader: form.receiptHeader, status: form.status
      })
    } else {
      await req.post('/property/projects', {
        orgCode: form.orgCode, orgName: form.projectName, companyName: form.companyName,
        contactName: form.contactName, contactPhone: form.contactPhone,
        servicePhone: form.servicePhone, address: form.address,
        receiptHeader: form.receiptHeader
      })
    }
    ElMessage.success(t('property.saved'))
    visible.value = false
    await store.loadProjects()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('property.saveFailed'))
  } finally { saving.value = false }
}
</script>

<style scoped>
.project-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; }
.page-title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.page-sub { font-size: 12px; color: #8492a6; margin-top: 4px; }
.spacer { flex: 1; }
</style>
