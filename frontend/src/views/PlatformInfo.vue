<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('platformInfo.title') }}</h3>
      <el-tag size="small" type="info">{{ t('misc5.current') }}</el-tag>
      <div class="spacer" />
      <el-button @click="load">{{ t('platformInfo.refresh') }}</el-button>
      <el-button type="primary" :loading="saving" @click="save">{{ t('platformInfo.save') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:14px"
              :title="t('misc3.platformTip')" />

    <el-row :gutter="18">
      <el-col :span="14">
        <el-form :model="form" label-width="110px" v-loading="loading">
          <el-form-item :label="t('platformInfo.code')">
            <el-input :model-value="form.tenantCode" disabled>
              <template #append>{{ t('misc5.readonly') }}</template>
            </el-input>
          </el-form-item>
          <el-form-item :label="t('platformInfo.name')" required>
            <el-input v-model="form.tenantName" maxlength="100" show-word-limit
                      :placeholder="t('platformInfo.nameHint')" />
          </el-form-item>
          <el-form-item :label="t('platformInfo.type')">
            <el-select v-model="form.tenantType" style="width:100%" disabled>
              <el-option :label="t('platformInfo.gov')" value="GOV" />
              <el-option :label="t('platformInfo.org')" value="ORG" />
              <el-option :label="t('platformInfo.enterprise')" value="ENTERPRISE" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('platformInfo.region')">
            <el-input :model-value="form.regionCode" disabled />
          </el-form-item>
          <el-form-item :label="t('platformInfo.isolation')">
            <el-input :model-value="form.isolationMode === 'ROW' ? t('misc5.rowIsolation') : (form.isolationMode || '—')" disabled />
          </el-form-item>
          <el-form-item :label="t('platformInfo.status')">
            <el-radio-group v-model="form.status" disabled>
              <el-radio-button value="ENABLED">{{ t('misc5.enable') }}</el-radio-button>
              <el-radio-button value="DISABLED">{{ t('misc5.disable') }}</el-radio-button>
            </el-radio-group>
            <div class="muted" style="font-size:12px;margin-top:4px">
              状态由平台运营设置，平台管理员不可修改。
            </div>
          </el-form-item>
        </el-form>
      </el-col>

      <el-col :span="10">
        <div class="side-card">
          <div class="side-title">{{ t('misc5.scopeTitle') }}</div>
          <ul>
            <li>{{ t('misc5.scopeCode') }}</li>
            <li>{{ t('misc5.scopeName') }}</li>
            <li>{{ t('misc5.scopeOrg') }}</li>
            <li>{{ t('misc5.scopeLessee') }}</li>
          </ul>
          <div class="side-title" style="margin-top:14px">{{ t('misc5.createdTitle') }}</div>
          <div class="muted">创建时间：{{ form.createTime || '—' }}</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { useAuthStore } from '@/store/auth'

const { t } = useI18n()
const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const form = reactive({
  id: null, tenantCode: '', tenantName: '', tenantType: 'GOV', regionCode: '',
  isolationMode: '', status: 'ENABLED', createTime: ''
})

async function load() {
  loading.value = true
  try {
    const d = await req.get('/platform/info')
    Object.assign(form, d || {})
  } catch (e) { /* 拦截器提示 */ } finally { loading.value = false }
}

async function save() {
  if (!form.tenantName) { ElMessage.warning('请填写平台名称'); return }
  if (form.status === 'DISABLED') {
    await ElMessageBox.confirm('停用后该平台将无法登录，确认停用？', '停用平台',
      { type: 'warning' })
  }
  saving.value = true
  try {
    // 平台侧仅允许修改名称
    await req.put('/platform/info', { tenantName: form.tenantName })
    ElMessage.success('平台信息已保存')
    await auth.loadMe()
    load()
  } catch (e) { /* 拦截器提示 */ } finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.side-card {
  background: var(--el-fill-color-lighter);
  border-radius: 10px;
  padding: 16px;
}
.side-title { font-weight: 600; margin-bottom: 8px; }
.side-card ul { margin: 0; padding-left: 18px; line-height: 2; font-size: 13px; color: var(--el-text-color-regular); }
</style>
