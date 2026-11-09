<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const items = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ feeCode: '', feeName: '', feeType: 'RENT', billingCycle: 'MONTHLY', unitPrice: 0, unitName: '月', taxRate: 0 })
const editing = ref(null)
const editForm = reactive({ feeName: '', feeType: 'RENT', billingCycle: 'MONTHLY', unitPrice: 0, unitName: '月', taxRate: 0 })
const typeName = (t) => ({ RENT: '租金', DEPOSIT: '押金', WATER: '水费', ELECTRICITY: '电费', GAS: '燃气费', SERVICE: '服务费', OTHER: '其他' }[t] || t)
const cycleName = (c) => ({ MONTHLY: '按月', QUARTERLY: '按季', YEARLY: '按年', ONE_TIME: '一次性' }[c] || c)
const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) items.value = await api.feeItems(project.value.id)
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.feeCode.trim() || !form.feeName.trim()) throw new Error('请填写费用编码和名称')
    await api.createFeeItem({
      projectId: project.value.id, feeCode: form.feeCode.trim(), feeName: form.feeName.trim(),
      feeType: form.feeType, billingCycle: form.billingCycle,
      unitPrice: Number(form.unitPrice || 0), unitName: form.unitName, taxRate: Number(form.taxRate || 0)
    })
    form.feeCode = ''; form.feeName = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


function openEdit(f) {
  editing.value = f
  Object.assign(editForm, { feeName: f.feeName || '', feeType: f.feeType || 'RENT', billingCycle: f.billingCycle || 'MONTHLY', unitPrice: f.unitPrice || 0, unitName: f.unitName || '', taxRate: f.taxRate || 0 })
}

async function saveEdit() {
  busy.value = true; error.value = ''
  try {
    if (!editForm.feeName.trim()) throw new Error('费用名称不能为空')
    await api.updateFeeItem(editing.value.id, { ...editForm })
    editing.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function toggle(item) {
  busy.value = true; error.value = ''
  try {
    await api.toggleFeeItem(item.id, item.feeStatus !== 'ENABLED')
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>计费项目</h2><p>{{ project?.orgName || '未选择项目' }} · 租金、押金、水电、服务费</p></div><span class="badge blue">{{ items.length }} 项</span></div>
      <div class="row">
        <div class="field"><label>费用编码</label><input v-model="form.feeCode" placeholder="如 RENT_STD" /></div>
        <div class="field"><label>费用名称</label><input v-model="form.feeName" placeholder="标准租金" /></div>
        <div class="field"><label>类型</label><select v-model="form.feeType"><option value="RENT">租金</option><option value="DEPOSIT">押金</option><option value="WATER">水费</option><option value="ELECTRICITY">电费</option><option value="GAS">燃气费</option><option value="SERVICE">服务费</option><option value="OTHER">其他</option></select></div>
        <div class="field"><label>周期</label><select v-model="form.billingCycle"><option value="MONTHLY">按月</option><option value="QUARTERLY">按季</option><option value="YEARLY">按年</option><option value="ONE_TIME">一次性</option></select></div>
        <div class="field"><label>单价</label><input v-model.number="form.unitPrice" type="number" /></div>
        <div class="field"><label>单位</label><input v-model="form.unitName" /></div>
        <div class="field"><label>税率</label><input v-model.number="form.taxRate" type="number" step="0.01" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('billing')" class="primary" :disabled="busy" @click="create">新增计费项</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>计费项目列表</h2><span class="small muted">停用后不再用于新账单</span></div>
      <div v-if="!items.length" class="empty">暂无计费项目</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>编码</th><th>名称</th><th>类型</th><th>周期</th><th>单价</th><th>单位</th><th>税率</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="f in items" :key="f.id">
              <td class="mono">{{ f.feeCode }}</td><td>{{ f.feeName }}</td><td>{{ typeName(f.feeType) }}</td>
              <td>{{ cycleName(f.billingCycle) }}</td><td>¥{{ money(f.unitPrice) }}</td><td>{{ f.unitName || '-' }}</td>
              <td>{{ f.taxRate }}</td>
              <td><span class="badge" :class="f.feeStatus === 'ENABLED' ? 'green' : 'orange'">{{ f.feeStatus }}</span></td>
              <td><button v-if="can('billing')" class="sm" @click="openEdit(f)">编辑</button> <button v-if="can('billing')" class="sm" @click="toggle(f)">{{ f.feeStatus === 'ENABLED' ? '停用' : '启用' }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <div class="panel-head"><h2>编辑计费项目</h2><button class="sm" @click="editing = null">关闭</button></div>
        <div class="field"><label>费用编码</label><input :value="editing.feeCode" disabled /></div>
        <div class="field"><label>费用名称</label><input v-model="editForm.feeName" /></div>
        <div class="field"><label>类型</label><select v-model="editForm.feeType"><option value="RENT">租金</option><option value="DEPOSIT">押金</option><option value="WATER">水费</option><option value="ELECTRICITY">电费</option><option value="GAS">燃气费</option><option value="SERVICE">服务费</option><option value="OTHER">其他</option></select></div>
        <div class="field"><label>周期</label><select v-model="editForm.billingCycle"><option value="MONTHLY">按月</option><option value="QUARTERLY">按季</option><option value="YEARLY">按年</option><option value="ONE_TIME">一次性</option></select></div>
        <div class="field"><label>单价</label><input v-model.number="editForm.unitPrice" type="number" /></div>
        <div class="field"><label>单位</label><input v-model="editForm.unitName" /></div>
        <div class="field"><label>税率</label><input v-model.number="editForm.taxRate" type="number" step="0.01" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveEdit">保存</button></div>
      </div>
    </div>
  </div>
</template>
