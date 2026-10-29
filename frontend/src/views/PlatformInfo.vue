<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">平台信息</h3>
      <el-tag size="small" type="info">当前平台</el-tag>
      <div class="spacer" />
      <el-button @click="load">刷新</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:14px"
              title="平台编码用于数据隔离，创建后不可修改；平台名称会显示在顶部与报表抬头。" />

    <el-row :gutter="18">
      <el-col :span="14">
        <el-form :model="form" label-width="110px" v-loading="loading">
          <el-form-item label="平台编码">
            <el-input :model-value="form.tenantCode" disabled>
              <template #append>不可修改</template>
            </el-input>
          </el-form-item>
          <el-form-item label="平台名称" required>
            <el-input v-model="form.tenantName" maxlength="100" show-word-limit
                      placeholder="如：漳州市住房保障中心" />
          </el-form-item>
          <el-form-item label="平台类型">
            <el-select v-model="form.tenantType" style="width:100%" disabled>
              <el-option label="政府" value="GOV" />
              <el-option label="运营机构" value="ORG" />
              <el-option label="企业" value="ENTERPRISE" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属区域">
            <el-input :model-value="form.regionCode" disabled />
          </el-form-item>
          <el-form-item label="隔离模式">
            <el-input :model-value="form.isolationMode === 'ROW' ? '行级隔离' : (form.isolationMode || '—')" disabled />
          </el-form-item>
          <el-form-item label="状态">
            <el-radio-group v-model="form.status" disabled>
              <el-radio-button value="ENABLED">启用</el-radio-button>
              <el-radio-button value="DISABLED">停用</el-radio-button>
            </el-radio-group>
            <div class="muted" style="font-size:12px;margin-top:4px">
              状态由平台运营设置，平台管理员不可修改。
            </div>
          </el-form-item>
        </el-form>
      </el-col>

      <el-col :span="10">
        <div class="side-card">
          <div class="side-title">口径说明</div>
          <ul>
            <li><b>平台编码</b>：数据隔离标识（登录时输入），不可修改</li>
            <li><b>平台名称</b>：顶部展示与报表抬头，可修改</li>
            <li><b>组织</b>：平台内的行政/运营单元，不等同于平台</li>
            <li><b>承租人</b>：租房子的人，属于业务对象，与平台无关</li>
          </ul>
          <div class="side-title" style="margin-top:14px">创建信息</div>
          <div class="muted">创建时间：{{ form.createTime || '—' }}</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { useAuthStore } from '@/store/auth'

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
