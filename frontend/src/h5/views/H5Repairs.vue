<template>
  <div>
    <div class="navbar"><span class="back" @click="$router.back()">←</span>{{ t('h5.repairTitle') }}</div>

    <div class="card">
      <el-form :model="form" label-position="top">
        <el-form-item :label="t('h5.issueType')">
          <el-select v-model="form.type" style="width:100%">
            <el-option :label="t('h5.waterElectric')" value="WATER_ELECTRIC" />
            <el-option :label="t('h5.doorWindow')" value="DOOR_WINDOW" />
            <el-option :label="t('h5.leak')" value="LEAK" />
            <el-option :label="t('h5.appliance')" value="APPLIANCE" />
            <el-option :label="t('h5.other')" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('h5.issueDesc')">
          <el-input v-model="form.description" type="textarea" :rows="4"
                    :placeholder="t('h5.descHint')" />
        </el-form-item>
        <el-form-item :label="t('h5.urgency')">
          <el-radio-group v-model="form.urgency">
            <el-radio value="NORMAL">{{ t('h5.normal') }}</el-radio>
            <el-radio value="URGENT">{{ t('h5.urgent') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-button type="primary" style="width:100%" :loading="saving"
                   @click="submit">{{ t('h5.submitRepair') }}</el-button>
      </el-form>
    </div>

    <div class="card">
      <b>{{ t('h5.repairNotes') }}</b>
      <div class="muted" style="margin-top:8px;line-height:1.7">
        {{ t('h5.note1') }}<br />
        {{ t('h5.note2') }}<br />
        {{ t('h5.note3') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { workOrderApi } from '@/api/modules'

const saving = ref(false)
const form = reactive({ type: 'WATER_ELECTRIC', description: '', urgency: 'NORMAL' })

async function submit() {
  if (!form.description) {
    ElMessage.warning('请填写问题描述')
    return
  }
  saving.value = true
  try {
    // 后端真实路径：POST /api/v1/workorders
    await workOrderApi.create({
      orderType: 'REPAIR',
      source: 'TENANT_APP',
      title: `住户报修：${form.type}`,
      description: form.description,
      priority: form.urgency,
      personId: localStorage.getItem('bp_person_id') || undefined
    })
    ElMessage.success('报修已提交')
    form.description = ''
  } catch (e) { /* 已提示 */ } finally {
    saving.value = false
  }
}
</script>
