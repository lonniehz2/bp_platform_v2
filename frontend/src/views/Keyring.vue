<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('keyring.title') }}</h3>
      <div class="spacer" />
      <el-input v-model="keyword" :placeholder="t('keyring.keyword')" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">{{ t('keyring.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('keyring.reset') }}</el-button>
      <el-button type="success" @click="createVisible = true">{{ t('keyring.create') }}</el-button>

    </div>

    <el-alert type="info" :closable="false" show-icon :title="'钥匙包绑定人员与通行介质；状态变更与回收需留痕'"
              style="margin-bottom:12px" />

    <el-table empty-text="暂无钥匙，先在「人员档案」建档再入包" :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="keyAlias" :label="t('keyring.alias')" width="140" />
      <el-table-column prop="personIdName" :label="t('keyring.holder')" width="120">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="keyStatus" :label="t('keyring.status')" width="110">
        <template #default="{ row }">{{ row.keyStatusLabel || enumLabel('keyStatus', row.keyStatus) }}</template>
      </el-table-column>
      <el-table-column :label="t('keyring.actions')" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('keyring.detail') }}</el-button>
          <el-button v-if="row.keyStatus === 'ACTIVE'" link type="warning"
                     @click="freeze(row)" data-testid="row-freeze">冻结</el-button>
          <el-button v-if="row.keyStatus === 'FROZEN'" link type="success"
                     @click="unfreeze(row)" data-testid="row-unfreeze">解冻</el-button>
          <el-button link @click="actPlain(row, '/keyring/{id}/status', '改状态')">{{ t('keyring.changeStatus') }}</el-button>
          <el-button link @click="actPlain(row, '/keyring/{id}/remove', '回收')">{{ t('keyring.recycle') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <el-dialog v-model="createVisible" :title="t('keyring.createTitle')" width="700px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="字段与后端 KeyringService.KeyringCmd 一致；带 * 为必填" />
      <el-form :model="form" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('keyring.personId')" required>
            <PersonPicker v-model="form.personId" width="240px" testid="person-picker" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('keyring.keyType')">
            <el-select v-model="form.keyType" style="width:100%" clearable data-testid="f-keyType">
              <el-option :label="t('keyring.face')" value="FACE" />
              <el-option :label="t('keyring.fingerprint')" value="FINGERPRINT" />
              <el-option :label="t('keyring.palm')" value="PALM_VEIN" />
              <el-option :label="t('keyring.password')" value="PASSWORD" />
              <el-option :label="t('keyring.card')" value="CARD" />
              <el-option :label="t('keyring.idcard')" value="IDCARD" />
              <el-option :label="t('keyring.qrcode')" value="QRCODE" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('keyring.alias')">
            <el-input v-model="form.keyAlias" data-testid="f-keyAlias"
                      :placeholder="t('keyring.aliasHint')" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('keyring.media')" required>
            <el-input v-model="form.channelValue" data-testid="f-channelValue"
                      :placeholder="t('keyring.mediaHint')" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('keyring.source')">
            <el-input v-model="form.keySource" placeholder="如 ALLOCATION / EXTRA" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('keyring.verifyWay')">
            <el-input v-model="form.verifyWay" placeholder="如 PASSWORD / CARD / FACE" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('keyring.syncScope')">
            <el-input v-model="form.syncScope" placeholder="如 HOUSE / BUILDING" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('keyring.expire')" required>
            <el-date-picker v-model="form.expireTime" type="datetime"
                            value-format="YYYY-MM-DD HH:mm:ss" style="width:100%"
                            data-testid="f-expireTime"
                            :placeholder="t('keyring.expireHint')" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('keyring.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('keyring.submit') }}</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('keyring.detail')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView，字段与中文名来自后端字段字典） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
const createVisible = ref(false)
/** 字段名严格对齐后端 KeyringService.KeyringCmd */
const form = reactive({
  personId: '',
  keyType: 'CARD',
  keyAlias: '',
  channelValue: '',
  keySource: '',
  verifyWay: '',
  syncScope: '',
  expireTime: '2027-12-31 23:59:59'
})

async function load() {
  loading.value = true
  try {
    const d = await req.get('/keyring', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  const missing = []
  if (!form.personId) missing.push('人员 ID')
  if (!form.channelValue) missing.push('介质值')
  if (missing.length) { ElMessage.warning('请填写：' + missing.join('、')); return }
  saving.value = true
  try {
    await req.post('/keyring', { ...form })
    ElMessage.success('创建成功')
    createVisible.value = false; load()
  } finally { saving.value = false }
}

/** 带原因的动作 */
async function actReason(row, path, label) {
  const { value } = await ElMessageBox.prompt('请输入' + label + '原因', label, {
    inputValue: ''
  })
  await req.post(`${pathTpl(path, row.id)}`, { reason: value })
  ElMessage.success(label + '成功'); load()
}
function pathTpl(p, id) { return p.replace('{id}', id) }

/** 无参数动作 */
async function actPlain(row, path, label) {
  await ElMessageBox.confirm('确认执行「' + label + '」？', label, { type: 'warning' })
  await req.post(pathTpl(path, row.id))
  ElMessage.success(label + '成功'); load()
}



function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}


/** 冻结 / 解冻钥匙 */
async function freeze(row) {
  await req.post(`/keyring/${row.id}/freeze`)
  ElMessage.success('已冻结')
  load()
}

async function unfreeze(row) {
  await req.post(`/keyring/${row.id}/unfreeze`)
  ElMessage.success('已解冻')
  load()
}

onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
