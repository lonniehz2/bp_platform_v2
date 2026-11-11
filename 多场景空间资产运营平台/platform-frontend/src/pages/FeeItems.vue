<script setup>
import { onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const items = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ feeCode: '', feeName: '', feeType: 'RENT', billingCycle: 'MONTHLY', unitPrice: 0, unitName: t('fee.monthUnit'), taxRate: 0 })
const editing = ref(null)
const editForm = reactive({ feeName: '', feeType: 'RENT', billingCycle: 'MONTHLY', unitPrice: 0, unitName: t('fee.monthUnit'), taxRate: 0 })
const typeName = (v) => ({ RENT: t('fee.rent'), DEPOSIT: t('fee.deposit'), WATER: t('fee.water'), ELECTRICITY: t('fee.electricity'), GAS: t('fee.gas'), SERVICE: t('fee.service'), OTHER: t('fee.other') }[v] || v)
const cycleName = (c) => ({ MONTHLY: t('fee.monthly'), QUARTERLY: t('fee.quarterly'), YEARLY: t('fee.yearly'), ONE_TIME: t('fee.oneTime') }[c] || c)
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
    if (!form.feeCode.trim() || !form.feeName.trim()) throw new Error(t('fee.required'))
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
    if (!editForm.feeName.trim()) throw new Error(t('fee.nameRequired'))
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
      <div class="panel-head"><div><h2>{{ t('fee.title') }}</h2><p>{{ project?.orgName || t('fee.noProject') }} · {{ t('fee.subtitle') }}</p></div><span class="badge blue">{{ items.length }} {{ t('fee.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('fee.code') }}</label><input v-model="form.feeCode" :placeholder="t('fee.codePlaceholder')" /></div>
        <div class="field"><label>{{ t('fee.name') }}</label><input v-model="form.feeName" :placeholder="t('fee.namePlaceholder')" /></div>
        <div class="field"><label>{{ t('fee.type') }}</label><select v-model="form.feeType"><option value="RENT">{{ t('fee.rent') }}</option><option value="DEPOSIT">{{ t('fee.deposit') }}</option><option value="WATER">{{ t('fee.water') }}</option><option value="ELECTRICITY">{{ t('fee.electricity') }}</option><option value="GAS">{{ t('fee.gas') }}</option><option value="SERVICE">{{ t('fee.service') }}</option><option value="OTHER">{{ t('fee.other') }}</option></select></div>
        <div class="field"><label>{{ t('fee.cycle') }}</label><select v-model="form.billingCycle"><option value="MONTHLY">{{ t('fee.monthly') }}</option><option value="QUARTERLY">{{ t('fee.quarterly') }}</option><option value="YEARLY">{{ t('fee.yearly') }}</option><option value="ONE_TIME">{{ t('fee.oneTime') }}</option></select></div>
        <div class="field"><label>{{ t('fee.price') }}</label><input v-model.number="form.unitPrice" type="number" /></div>
        <div class="field"><label>{{ t('fee.unit') }}</label><input v-model="form.unitName" /></div>
        <div class="field"><label>{{ t('fee.tax') }}</label><input v-model.number="form.taxRate" type="number" step="0.01" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('billing')" class="primary" :disabled="busy" @click="create">{{ t('fee.add') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('fee.list') }}</h2><span class="small muted">{{ t('fee.listHint') }}</span></div>
      <div v-if="!items.length" class="empty">{{ t('fee.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('fee.code') }}</th><th>{{ t('fee.name') }}</th><th>{{ t('fee.type') }}</th><th>{{ t('fee.cycle') }}</th><th>{{ t('fee.price') }}</th><th>{{ t('fee.unit') }}</th><th>{{ t('fee.tax') }}</th><th>{{ t('fee.status') }}</th><th>{{ t('fee.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="f in items" :key="f.id">
              <td class="mono">{{ f.feeCode }}</td><td>{{ f.feeName }}</td><td>{{ typeName(f.feeType) }}</td>
              <td>{{ cycleName(f.billingCycle) }}</td><td>¥{{ money(f.unitPrice) }}</td><td>{{ f.unitName || '-' }}</td>
              <td>{{ f.taxRate }}</td>
              <td><span class="badge" :class="f.feeStatus === 'ENABLED' ? 'green' : 'orange'">{{ enumLabel(f.feeStatus) }}</span></td>
              <td><button v-if="can('billing')" class="sm" @click="openEdit(f)">{{ t('fee.edit') }}</button> <button v-if="can('billing')" class="sm" @click="toggle(f)">{{ f.feeStatus === 'ENABLED' ? t('fee.disable') : t('fee.enable') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('fee.editTitle') }}</h2><button class="sm" @click="editing = null">{{ t('fee.close') }}</button></div>
        <div class="field"><label>{{ t('fee.code') }}</label><input :value="editing.feeCode" disabled /></div>
        <div class="field"><label>{{ t('fee.name') }}</label><input v-model="editForm.feeName" /></div>
        <div class="field"><label>{{ t('fee.type') }}</label><select v-model="editForm.feeType"><option value="RENT">{{ t('fee.rent') }}</option><option value="DEPOSIT">{{ t('fee.deposit') }}</option><option value="WATER">{{ t('fee.water') }}</option><option value="ELECTRICITY">{{ t('fee.electricity') }}</option><option value="GAS">{{ t('fee.gas') }}</option><option value="SERVICE">{{ t('fee.service') }}</option><option value="OTHER">{{ t('fee.other') }}</option></select></div>
        <div class="field"><label>{{ t('fee.cycle') }}</label><select v-model="editForm.billingCycle"><option value="MONTHLY">{{ t('fee.monthly') }}</option><option value="QUARTERLY">{{ t('fee.quarterly') }}</option><option value="YEARLY">{{ t('fee.yearly') }}</option><option value="ONE_TIME">{{ t('fee.oneTime') }}</option></select></div>
        <div class="field"><label>{{ t('fee.price') }}</label><input v-model.number="editForm.unitPrice" type="number" /></div>
        <div class="field"><label>{{ t('fee.unit') }}</label><input v-model="editForm.unitName" /></div>
        <div class="field"><label>{{ t('fee.tax') }}</label><input v-model.number="editForm.taxRate" type="number" step="0.01" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveEdit">{{ t('fee.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
