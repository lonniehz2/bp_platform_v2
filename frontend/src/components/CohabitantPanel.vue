<template>
  <div>
    <div class="toolbar">
      <el-tag size="small" type="info">保障人口影响配租面积与补贴额度</el-tag>
      <el-tag size="small">家庭人口：{{ householdSize }}</el-tag>
      <div class="spacer" />
      <el-button type="success" size="small" @click="openCreate">登记同住人</el-button>
      <el-button size="small" @click="loadAll">刷新</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="memberName" label="姓名" width="120" />
      <el-table-column prop="relation" label="关系" width="110">
        <template #default="{ row }">{{ enumLabel('relation', row.relation) }}</template>
      </el-table-column>
      <el-table-column prop="idCardMask" label="证件号(脱敏)" width="180" />
      <el-table-column label="门禁授权" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="Number(row.isGranted) === 1 ? 'success' : 'info'">
            {{ Number(row.isGranted) === 1 ? '已授权' : '未授权' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary"
                     @click="toggleGrant(row)">
            {{ Number(row.isGranted) === 1 ? '取消授权' : '授予门禁' }}
          </el-button>
          <el-button link type="danger" @click="remove(row)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" title="登记同住人" width="520px">
      <el-form :model="f" label-width="110px">
        <el-form-item label="姓名" required>
          <el-input v-model="f.memberName" /></el-form-item>
        <el-form-item label="关联人员ID">
          <el-input v-model="f.personId" placeholder="已有人员档案时填写" />
        </el-form-item>
        <el-form-item label="证件号(脱敏)">
          <el-input v-model="f.idCardMask" placeholder="如 3506**********1234" />
        </el-form-item>
        <el-form-item label="与承租人关系">
          <el-select v-model="f.relation" style="width:100%">
            <el-option label="配偶" value="SPOUSE" />
            <el-option label="子女" value="CHILD" />
            <el-option label="父母" value="PARENT" />
            <el-option label="其他亲属" value="RELATIVE" />
            <el-option label="其他" value="OTHER" />
          </el-select></el-form-item>
        <el-form-item label="同步门禁授权">
          <el-switch v-model="f.isGranted" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

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
  if (!f.memberName) { ElMessage.warning('请填写同住人姓名'); return }
  saving.value = true
  try {
    await req.post(`/contracts/${props.contractId}/cohabitants`, { ...f })
    ElMessage.success('已登记')
    visible.value = false; loadAll()
  } finally { saving.value = false }
}

async function toggleGrant(row) {
  const granted = Number(row.isGranted) !== 1
  await req.post(
    `/contracts/${props.contractId}/cohabitants/${row.id}/grant`, { granted })
  ElMessage.success(granted ? '已授予门禁' : '已取消授权'); loadAll()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认移除同住人「${row.memberName}」？`, '移除确认',
    { type: 'warning' })
  await req.delete(`/contracts/${props.contractId}/cohabitants/${row.id}`)
  ElMessage.success('已移除'); loadAll()
}

watch(() => props.contractId, loadAll, { immediate: true })
</script>
