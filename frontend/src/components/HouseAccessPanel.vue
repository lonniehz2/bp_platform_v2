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
      </el-table>

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

const props = defineProps({ modelValue: Boolean, houseId: [String, Number] })
const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const panel = ref({})
const tempVisible = ref(false)
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
    panel.value = await req.get('/house-access/' + id)
    if (!voiceText.value) voiceText.value = defaultVoice.value
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('houseAccess.loadFailed'))
  } finally { loading.value = false }
}

async function freeze() {
  await ElMessageBox.confirm(t('houseAccess.freezeConfirm'), t('houseAccess.freeze'),
    { type: 'warning' })
  saving.value = true
  try {
    const r = await req.post(`/house-access/${props.houseId}/freeze`, { reason: t('houseAccess.manualFreeze') })
    ElMessage.success(t('houseAccess.frozen', { n: r.revoked || 0 }))
    await load(props.houseId)
  } finally { saving.value = false }
}

async function restore() {
  if (!panel.value.contract) {
    ElMessage.warning(t('houseAccess.noContract'))
    return
  }
  saving.value = true
  try {
    await req.post(`/house-access/${props.houseId}/restore`)
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
