<template>
  <el-dialog v-model="visible" :title="t('houseAccess.title')" width="820px">
    <div v-loading="loading">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item :label="t('houseAccess.house')">
          {{ panel.house?.houseName || panel.house?.houseCode || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('houseAccess.status')">
          {{ enumLabel('houseStatus', panel.house?.houseStatus) || panel.house?.houseStatus || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('houseAccess.contract')">
          {{ panel.contract?.contractNo || t('houseAccess.noContract') }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('houseAccess.lessee')">
          {{ panel.contract?.lesseeName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('houseAccess.devices')">
          {{ panel.deviceCount ?? 0 }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('houseAccess.entitlements')">
          {{ panel.entitlements?.length || 0 }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="toolbar" style="margin:14px 0 8px">
        <el-button type="danger" plain :loading="saving" @click="freeze">
          {{ t('houseAccess.freeze') }}
        </el-button>
        <el-button type="success" plain :loading="saving" @click="restore">
          {{ t('houseAccess.restore') }}
        </el-button>
        <el-button type="warning" plain @click="tempVisible = true">
          {{ t('houseAccess.temp') }}
        </el-button>
        <el-button type="primary" plain @click="personVisible = true">
          {{ t('houseAccess.personAuth') }}
        </el-button>
        <el-button type="primary" plain :loading="saving" @click="emergency">
          {{ t('houseAccess.emergency') }}
        </el-button>
      </div>

      <el-table :data="panel.entitlements || []" border size="small" max-height="260"
                :empty-text="t('houseAccess.noEntitlement')">
        <el-table-column prop="grantNo" :label="t('houseAccess.grantNo')" width="180" />
        <el-table-column prop="grantLevel" :label="t('houseAccess.level')" width="110" />
        <el-table-column prop="validEnd" :label="t('houseAccess.validEnd')" width="170" />
        <el-table-column prop="grantStatus" :label="t('houseAccess.status')" width="110">
          <template #default="{ row }">{{ enumLabel('grantStatus', row.grantStatus) }}</template>
        </el-table-column>
        <el-table-column prop="freezeReason" :label="t('houseAccess.reason')" min-width="140" />
        <el-table-column :label="t('houseAccess.actions')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.grantStatus !== 'FROZEN'" link type="danger"
                       @click="freezePerson(row)">{{ t('houseAccess.freeze') }}</el-button>
            <el-button v-else link type="success"
                       @click="restorePerson(row)">{{ t('houseAccess.restore') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-divider content-position="left">{{ t('houseAccess.keys') }}</el-divider>
      <el-table :data="panel.keyrings || []" border size="small" max-height="180"
                :empty-text="t('houseAccess.noKeys')">
        <el-table-column prop="keyType" :label="t('houseAccess.keyType')" width="120" />
        <el-table-column prop="keyAlias" :label="t('houseAccess.keyAlias')" min-width="130" />
        <el-table-column prop="keyStatus" :label="t('houseAccess.keyStatus')" width="100" />
        <el-table-column :label="t('houseAccess.actions')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.keyStatus !== 'FROZEN'" link type="danger"
                       @click="freezeKey(row)">{{ t('houseAccess.freeze') }}</el-button>
            <el-button v-else link type="success"
                       @click="restoreKey(row)">{{ t('houseAccess.restore') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="personVisible" :title="t('houseAccess.personAuth')" width="500px" append-to-body>
        <el-form label-width="100px">
          <el-form-item :label="t('houseAccess.person')" required>
            <PersonPicker v-model="personForm.personId" width="100%" />
          </el-form-item>
          <el-form-item :label="t('houseAccess.validEnd')" required>
            <el-date-picker v-model="personForm.validEnd" type="datetime"
                            value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
          </el-form-item>
          <el-form-item :label="t('houseAccess.reason')" required>
            <el-input v-model="personForm.reason" type="textarea" :rows="2" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="personVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" :loading="saving" @click="personAuthorize">
            {{ t('houseAccess.authorize') }}
          </el-button>
        </template>
      </el-dialog>

      <el-divider content-position="left">{{ t('houseAccess.voice') }}</el-divider>
      <div style="display:flex;gap:8px">
        <el-input v-model="voiceText" :placeholder="t('houseAccess.voiceHint')" />
        <el-button @click="speak">{{ t('houseAccess.speak') }}</el-button>
      </div>

      <el-dialog v-model="tempVisible" :title="t('houseAccess.tempTitle')" width="460px" append-to-body>
        <el-form label-width="100px">
          <el-form-item :label="t('houseAccess.level')">
            <el-select v-model="tempForm.grantLevel" style="width:100%">
              <el-option label="VISIT" value="VISIT" />
              <el-option label="USAGE" value="USAGE" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('houseAccess.validEnd')">
            <el-date-picker v-model="tempForm.validEnd" type="datetime"
                            value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="tempVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" :loading="saving" @click="temporary">
            {{ t('common.confirm') }}
          </el-button>
        </template>
      </el-dialog>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'
import PersonPicker from '@/components/PersonPicker.vue'

const props = defineProps({ modelValue: Boolean, houseId: [String, Number] })
const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const panel = ref({})
const tempVisible = ref(false)
const personVisible = ref(false)
const personForm = reactive({ personId: '', validEnd: '', reason: '' })
const voiceText = ref('')
const tempForm = reactive({ grantLevel: 'VISIT', validEnd: '' })
const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const defaultVoice = computed(() => t('houseAccess.defaultVoice', {
  house: panel.value.house?.houseName || panel.value.house?.houseCode || '',
  person: panel.value.contract?.lesseeName || ''
}))
watch(defaultVoice, (v) => { if (!voiceText.value) voiceText.value = v }, { immediate: true })
watch(() => [props.modelValue, props.houseId], async ([v, id]) => {
  if (v && id) await load(id)
})

async function load(id) {
  loading.value = true
  try {
    panel.value = await req.get(`/house-access/${id}`)
    if (!voiceText.value) voiceText.value = defaultVoice.value
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('houseAccess.loadFailed'))
  } finally { loading.value = false }
}

async function freeze() {
  const { value } = await ElMessageBox.prompt(t('houseAccess.freezeReason'), t('houseAccess.freeze'),
    { inputPlaceholder: t('houseAccess.reasonHint'), inputValidator: (v) => !!(v && v.trim()) })
  saving.value = true
  try {
    const r = await req.post(`/house-access/${props.houseId}/freeze`, { reason: value })
    ElMessage.success(t('houseAccess.frozen', { n: r.frozen || 0 }))
    await load(props.houseId)
  } finally { saving.value = false }
}

async function restore() {
  const { value } = await ElMessageBox.prompt(t('houseAccess.restoreReason'), t('houseAccess.restore'),
    { inputPlaceholder: t('houseAccess.reasonHint'), inputValidator: (v) => !!(v && v.trim()) })
  saving.value = true
  try {
    await req.post(`/house-access/${props.houseId}/restore`, { reason: value })
    ElMessage.success(t('houseAccess.restored'))
    await load(props.houseId)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('houseAccess.restoreFailed'))
  } finally { saving.value = false }
}

async function temporary() {
  if (!tempForm.validEnd) {
    ElMessage.warning(t('houseAccess.validEnd'))
    return
  }
  saving.value = true
  try {
    await req.post(`/house-access/${props.houseId}/temporary`, {
      personId: panel.value.contract?.personId,
      grantLevel: tempForm.grantLevel,
      validEnd: tempForm.validEnd
    })
    ElMessage.success(t('houseAccess.tempCreated'))
    tempVisible.value = false
    await load(props.houseId)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('houseAccess.tempFailed'))
  } finally { saving.value = false }
}

async function freezeKey(row) {
  const { value } = await ElMessageBox.prompt(t('houseAccess.freezeReason'), t('houseAccess.freeze'),
    { inputPlaceholder: t('houseAccess.reasonHint'), inputValidator: (v) => !!(v && v.trim()) })
  await req.post(`/house-access/${props.houseId}/keys/${row.id}/freeze`, { reason: value })
  ElMessage.success(t('houseAccess.done'))
  await load(props.houseId)
}

async function restoreKey(row) {
  const { value } = await ElMessageBox.prompt(t('houseAccess.restoreReason'), t('houseAccess.restore'),
    { inputPlaceholder: t('houseAccess.reasonHint'), inputValidator: (v) => !!(v && v.trim()) })
  await req.post(`/house-access/${props.houseId}/keys/${row.id}/restore`, { reason: value })
  ElMessage.success(t('houseAccess.done'))
  await load(props.houseId)
}

async function freezePerson(row) {
  if (!row.personId) {
    ElMessage.warning(t('houseAccess.noPerson'))
    return
  }
  const { value } = await ElMessageBox.prompt(t('houseAccess.freezeReason'), t('houseAccess.freeze'),
    { inputPlaceholder: t('houseAccess.reasonHint'), inputValidator: (v) => !!(v && v.trim()) })
  await req.post(`/house-access/${props.houseId}/persons/${row.personId}/freeze`, { reason: value })
  ElMessage.success(t('houseAccess.done'))
  await load(props.houseId)
}

async function restorePerson(row) {
  if (!row.personId) {
    ElMessage.warning(t('houseAccess.noPerson'))
    return
  }
  const { value } = await ElMessageBox.prompt(t('houseAccess.restoreReason'), t('houseAccess.restore'),
    { inputPlaceholder: t('houseAccess.reasonHint'), inputValidator: (v) => !!(v && v.trim()) })
  await req.post(`/house-access/${props.houseId}/persons/${row.personId}/restore`, { reason: value })
  ElMessage.success(t('houseAccess.done'))
  await load(props.houseId)
}

async function personAuthorize() {
  if (!personForm.personId || !personForm.validEnd || !personForm.reason.trim()) {
    ElMessage.warning(t('houseAccess.personAuthHint'))
    return
  }
  saving.value = true
  try {
    const r = await req.post(`/house-access/${props.houseId}/person-authorize`, {
      personId: personForm.personId,
      validEnd: personForm.validEnd,
      reason: personForm.reason
    })
    ElMessage.success(t('houseAccess.authorized', { n: r.keyringCount || 0 }))
    personVisible.value = false
    personForm.personId = ''
    personForm.validEnd = ''
    personForm.reason = ''
    await load(props.houseId)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('houseAccess.authorizeFailed'))
  } finally { saving.value = false }
}

async function emergency() {
  saving.value = true
  try {
    const r = await req.post(`/house-access/${props.houseId}/emergency-password`, { hours: 24 })
    ElMessageBox.alert(
      `${t('houseAccess.code')}: ${r.code}\n${t('houseAccess.expire')}: ${r.expireTime}`,
      t('houseAccess.emergency'), { type: 'success' })
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('houseAccess.emergencyFailed'))
  } finally { saving.value = false }
}

function speak() {
  if (!('speechSynthesis' in window)) {
    ElMessage.warning(t('houseAccess.voiceUnsupported'))
    return
  }
  const u = new SpeechSynthesisUtterance(voiceText.value || defaultVoice.value)
  u.lang = 'zh-CN'
  u.rate = 1
  window.speechSynthesis.cancel()
  window.speechSynthesis.speak(u)
}
</script>
