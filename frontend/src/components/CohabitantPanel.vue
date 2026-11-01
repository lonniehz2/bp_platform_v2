<template>
  <div>
    <div class="toolbar">
      <el-tag size="small" type="info">{{ t('cohab.tip') }}</el-tag>
      <el-tag size="small">{{ t('cohab.household', { n: householdSize }) }}</el-tag>
      <div class="spacer" />
      <el-button type="success" size="small" @click="openCreate">{{ t('cohab.add') }}</el-button>
      <el-button size="small" @click="loadAll">{{ t('cohab.refresh') }}</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="memberName" :label="t('cohab.name')" width="120" />
      <el-table-column prop="relation" :label="t('cohab.relation')" width="110">
        <template #default="{ row }">{{ enumLabel('relation', row.relation) }}</template>
      </el-table-column>
      <el-table-column prop="idCardMask" :label="t('cohab.idCard')" width="180" />
      <el-table-column :label="t('cohab.access')" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="Number(row.isGranted) === 1 ? 'success' : 'info'">
            {{ Number(row.isGranted) === 1 ? t('cohab.granted') : t('cohab.notGranted') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('cohab.actions')" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary"
                     @click="toggleGrant(row)">
            {{ Number(row.isGranted) === 1 ? t('cohab.revoke') : t('cohab.grant') }}
          </el-button>
          <el-button link type="danger" @click="remove(row)">{{ t('cohab.remove') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" :title="t('cohab.createTitle')" width="520px">
      <el-form :model="f" label-width="110px">
        <el-form-item :label="t('cohab.name')" required>
          <el-input v-model="f.memberName" /></el-form-item>
        <el-form-item :label="t('cohab.personId')">
          <el-input v-model="f.personId" :placeholder="t('cohab.personHint')" />
        </el-form-item>
        <el-form-item :label="t('cohab.idCard')">
          <el-input v-model="f.idCardMask" :placeholder="t('cohab.idCardHint')" />
        </el-form-item>
        <el-form-item :label="t('cohab.relationLabel')">
          <el-select v-model="f.relation" style="width:100%">
            <el-option :label="t('cohab.spouse')" value="SPOUSE" />
            <el-option :label="t('cohab.child')" value="CHILD" />
            <el-option :label="t('cohab.parent')" value="PARENT" />
            <el-option :label="t('cohab.relative')" value="RELATIVE" />
            <el-option :label="t('cohab.other')" value="OTHER" />
          </el-select></el-form-item>
        <el-form-item :label="t('cohab.syncAccess')">
          <el-switch v-model="f.isGranted" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">{{ t('cohab.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('cohab.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

const { t } = useI18n()
const props = defineProps({ contractId: { type: [String, Number], default: null } })

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const householdSize = ref(0)
const visible = ref(false)
const f = reactive({ personId: null, memberName: '', idCardMask: '',
  relation: 'SPOUSE', isGranted: 0 })

async function loadAll() {
  if (!props.contractId) return
  loading.value = true
  try {
    const d = await req.get(`/contracts/${props.contractId}/cohabitants`)
    rows.value = Array.isArray(d) ? d : (d.rows || [])
    const hs = await req.get(
      `/contracts/${props.contractId}/cohabitants/household-size`)
    householdSize.value = typeof hs === 'number' ? hs
      : (hs?.householdSize ?? hs?.size ?? rows.value.length + 1)
  } catch (e) { rows.value = [] } finally { loading.value = false }
}

function openCreate() {
  Object.assign(f, { personId: null, memberName: '', idCardMask: '',
    relation: 'SPOUSE', isGranted: 0 })
  visible.value = true
}

async function doCreate() {
  if (!f.memberName) { ElMessage.warning(t('cohab.nameRequired')); return }
  saving.value = true
  try {
    await req.post(`/contracts/${props.contractId}/cohabitants`, { ...f })
    ElMessage.success(t('cohab.created'))
    visible.value = false; loadAll()
  } finally { saving.value = false }
}

async function toggleGrant(row) {
  const granted = Number(row.isGranted) !== 1
  await req.post(
    `/contracts/${props.contractId}/cohabitants/${row.id}/grant`, { granted })
  ElMessage.success(granted ? t('cohab.grantedMsg') : t('cohab.revokedMsg')); loadAll()
}

async function remove(row) {
  await ElMessageBox.confirm(t('cohab.removeConfirm', { name: row.memberName }), t('cohab.removeTitle'),
    { type: 'warning' })
  await req.delete(`/contracts/${props.contractId}/cohabitants/${row.id}`)
  ElMessage.success(t('cohab.removed')); loadAll()
}

watch(() => props.contractId, loadAll, { immediate: true })
</script>
