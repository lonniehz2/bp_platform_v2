<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import TreeSelect from '../components/TreeSelect.vue'
import { confirmAction } from '../confirm'
import { can, canAction } from '../permissions'
import DataTable from '../components/DataTable.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const devices = ref([])
const page = ref(1)
const deviceQuery = ref('')
const persons = ref([])
const spaces = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ deviceCode: '', deviceName: '', deviceType: 'LOCK', spaceId: '', deviceModel: '', installTime: '', warrantyEnd: '' })
const grantForm = reactive({ personId: '', targetId: '', validStart: '2026-11-08', validEnd: '2027-11-07' })
const grants = ref([])
const editingDevice = ref(null)
const detailDevice = ref(null)
const deviceEditForm = reactive({ deviceName: '', deviceType: 'LOCK', deviceModel: '', installTime: '', warrantyEnd: '', remark: '' })

const money = (v) => Number(v || 0).toLocaleString('zh-CN')
const filteredDevices = computed(() => {
  const q = deviceQuery.value.trim().toLowerCase()
  if (!q) return devices.value
  return devices.value.filter(d => (String(d.deviceCode) + ' ' + String(d.deviceName || '') + ' ' + String(d.deviceMac || '') + ' ' + String(d.spaceName || '')).toLowerCase().includes(q))
})
const pagedDevices = computed(() => filteredDevices.value.slice((page.value - 1) * 10, page.value * 10))
const deviceColumns = [
  { key: 'deviceCode', title: t('dev.code'), width: '150px' },
  { key: 'deviceName', title: t('dev.name'), width: '130px' },
  { key: 'deviceType', title: t('dev.type'), width: '80px' },
  { key: 'deviceModel', title: t('dev.model'), width: '110px' },
  { key: 'deviceMac', title: 'MAC', width: '150px' },
  { key: 'spaceName', title: t('dev.space'), width: '140px' },
  { key: 'installStatus', title: t('dev.install'), width: '90px' },
  { key: 'warrantyEnd', title: t('dev.warranty'), width: '110px' },
  { key: 'assetStatus', title: t('dev.status'), width: '90px' },
  { key: 'businessStatus', title: t('dev.status'), width: '90px' },
  { key: 'actions', title: t('dev.action'), width: '220px' }
]

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  if (chosen) return chosen
  const demo = all.find(p => p.orgCode === 'DEMO_PROJECT')
  if (demo) return demo
  return all.slice().sort((a, b) =>
    ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
    ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
  )[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    localStorage.setItem('platformProjectId', project.value.id)
    const [d, p, s] = await Promise.all([
      api.devices(project.value.id), api.persons(), api.spaces(project.value.id)
    ])
    devices.value = d; persons.value = p; spaces.value = s
    if (!form.spaceId && s.length) form.spaceId = s[0].id
    if (!grantForm.personId && p.length) grantForm.personId = p[0].id
    if (!grantForm.targetId && s.length) grantForm.targetId = s[0].id
    await loadGrants()
  } catch (e) { error.value = e.message }
}

async function createDevice() {
  busy.value = true; error.value = ''
  try {
    if (!form.deviceCode.trim()) throw new Error(t('dev.requiredCode'))
    await api.createDevice({
      projectId: project.value.id, spaceId: form.spaceId || null,
      deviceCode: form.deviceCode.trim(), deviceName: form.deviceName || form.deviceCode,
      deviceType: form.deviceType, deviceModel: form.deviceModel, installTime: form.installTime || null,
      warrantyEnd: form.warrantyEnd || null, assetStatus: 'ACTIVE', businessStatus: 'IN_USE'
    })
    form.deviceCode = ''; form.deviceName = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function loadGrants() {
  if (!grantForm.personId) { grants.value = []; return }
  try { grants.value = await api.grants(grantForm.personId) } catch { grants.value = [] }
}

async function createGrant() {
  busy.value = true; error.value = ''
  try {
    await api.createGrant({
      projectId: project.value.id, personId: grantForm.personId,
      targetType: 'SPACE', targetId: grantForm.targetId,
      grantLevel: 'OPEN', validStart: grantForm.validStart, validEnd: grantForm.validEnd,
      sourceType: 'MANUAL'
    })
    error.value = ''
    await loadGrants()
    alert(t('dev.grantCreated'))
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function revokeGrant(g) {
  busy.value = true; error.value = ''
  try { await api.revokeGrant(g.id, t('dev.revokeReason')); await loadGrants() } catch (e) { error.value = e.message } finally { busy.value = false }
}



function openDeviceEdit(d) {
  editingDevice.value = d
  Object.assign(deviceEditForm, {
    deviceName: d.deviceName || '', deviceType: d.deviceType || 'LOCK', deviceModel: d.deviceModel || '',
    installTime: d.installTime || '', warrantyEnd: d.warrantyEnd || '', remark: d.remark || ''
  })
}

async function saveDeviceEdit() {
  busy.value = true; error.value = ''
  try {
    if (!deviceEditForm.deviceName.trim()) throw new Error(t('dev.requiredName'))
    await api.updateDevice(editingDevice.value.id, { ...deviceEditForm })
    editingDevice.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function archiveDevice(d) {
  if (!await confirmAction({ title: t('dev.archiveTitle'), message: t('dev.archiveMessage', { code: d.deviceCode }), confirmText: t('dev.archiveConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.archiveDevice(d.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function repairDevice(d) {
  if (!await confirmAction({ title: t('dev.repairTitle'), message: t('dev.repairMessage', { code: d.deviceCode }), confirmText: t('dev.repairConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.repairDevice(d.id, { reason: t('dev.repairReason') }); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function enableDevice(d) {
  if (!await confirmAction({ title: t('dev.enableTitle'), message: t('dev.enableMessage', { code: d.deviceCode }), confirmText: t('dev.enableConfirm') })) return
  busy.value = true; error.value = ''
  try { await api.enableDevice(d.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">{{ t('dev.createProject') }}</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>{{ t('dev.title') }}</h2><p>{{ project.orgName }} · {{ t('dev.subtitle') }}</p></div><span class="pill">DEVICE</span></div>
        <div class="row">
          <div class="field"><label>{{ t('dev.code') }}</label><input v-model="form.deviceCode" :placeholder="t('dev.codePlaceholder')" /></div>
          <div class="field"><label>{{ t('dev.name') }}</label><input v-model="form.deviceName" :placeholder="t('dev.namePlaceholder')" /></div>
          <div class="field"><label>{{ t('dev.type') }}</label>
            <select v-model="form.deviceType"><option value="LOCK">{{ t('dev.lock') }}</option><option value="METER">{{ t('dev.meter') }}</option><option value="ELEVATOR">{{ t('dev.elevator') }}</option><option value="GATE">{{ t('dev.gate') }}</option></select>
          </div>
          <div class="field"><label>{{ t('dev.model') }}</label><input v-model="form.deviceModel" /></div>
          <div class="field"><label>{{ t('dev.install') }}</label><input v-model="form.installTime" type="datetime-local" /></div>
          <div class="field"><label>{{ t('dev.warranty') }}</label><input v-model="form.warrantyEnd" type="date" /></div>
          <div class="field"><label>{{ t('dev.space') }}</label>
            <TreeSelect v-model="form.spaceId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" :placeholder="t('dev.selectSpace')" />
          </div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="canAction('device:create', 'device')" class="primary" :disabled="busy" @click="createDevice">{{ t('dev.add') }}</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('dev.list') }}</h2><span class="small muted">{{ devices.length }} {{ t('dev.count') }}</span></div>
        <div class="row" style="margin-bottom:8px">
          <input v-model="deviceQuery" :placeholder="t('dev.search')" style="max-width:320px" @input="page = 1" />
        </div>
        <DataTable :rows="pagedDevices" :columns="deviceColumns" :page="page" :page-size="10" :total="filteredDevices.length" :empty-text="t('dev.empty')" @update:page="page = $event">
          <template #cell-assetStatus="{ row }"><span class="badge green">{{ row.assetStatus }}</span></template>
          <template #cell-actions="{ row }">
            <button class="sm" @click="openDeviceEdit(row)">{{ t('dev.edit') }}</button>
            <RouterLink class="sm" :to="`/guarantee/detail/DEVICE/${row.id}`">{{ t('dev.detail') }}</RouterLink>
            <button v-if="canAction('device:archive', 'device')" class="sm danger" :disabled="busy" @click="archiveDevice(row)">{{ t('dev.archive') }}</button>
            <button v-if="canAction('device:repair', 'device') && row.businessStatus !== 'FAULT'" class="sm" :disabled="busy" @click="repairDevice(row)">{{ t('dev.repair') }}</button>
            <button v-if="canAction('device:enable', 'device') && ['FAULT','DISABLED'].includes(row.businessStatus)" class="sm primary" :disabled="busy" @click="enableDevice(row)">{{ t('dev.enable') }}</button>
          </template>
        </DataTable>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('dev.grantTitle') }}</h2><span class="small muted">{{ t('dev.grantHint') }}</span></div>
        <div class="row">
          <div class="field"><label>{{ t('dev.person') }}</label>
            <SearchSelect v-model="grantForm.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('dev.searchPerson')" @change="loadGrants" />
          </div>
          <div class="field"><label>{{ t('dev.grantSpace') }}</label>
            <TreeSelect v-model="grantForm.targetId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" :placeholder="t('dev.selectGrantSpace')" />
          </div>
          <div class="field"><label>{{ t('dev.start') }}</label><input v-model="grantForm.validStart" type="date" /></div>
          <div class="field"><label>{{ t('dev.end') }}</label><input v-model="grantForm.validEnd" type="date" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="canAction('device:grant', 'device')" class="primary" :disabled="busy" @click="createGrant">{{ t('dev.addGrant') }}</button></div>
        </div>
        <div v-if="grants.length" class="table-wrap" style="margin-top:12px">
          <table>
            <thead><tr><th>{{ t('dev.typeCol') }}</th><th>{{ t('dev.target') }}</th><th>{{ t('dev.level') }}</th><th>{{ t('dev.validity') }}</th><th>{{ t('dev.status') }}</th><th>{{ t('dev.action') }}</th></tr></thead>
            <tbody>
              <tr v-for="g in grants" :key="g.id">
                <td>{{ g.targetType }}</td><td class="mono">{{ g.targetId }}</td><td>{{ g.grantLevel }}</td>
                <td class="small">{{ g.validStart }} ~ {{ g.validEnd || t('dev.longTerm') }}</td>
                <td><span class="badge" :class="g.grantStatus === 'ACTIVE' ? 'green' : 'orange'">{{ g.grantStatus }}</span></td>
                <td><button v-if="canAction('device:grant', 'device') && g.grantStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="revokeGrant(g)">{{ t('dev.revoke') }}</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty">{{ t('dev.emptyGrant') }}</div>
      </div>
    </template>

    <div v-if="detailDevice" class="modal-mask" @click.self="detailDevice = null">
      <div class="modal" style="max-width:720px">
        <div class="panel-head"><div><h2>{{ detailDevice.deviceName }}</h2><p class="small muted">{{ detailDevice.deviceCode }}</p></div><button class="sm" @click="detailDevice = null">{{ t('dev.close') }}</button></div>
        <EntityDetailTabs type="DEVICE" :entity-id="detailDevice.id" />
      </div>
    </div>

    <div v-if="editingDevice" class="modal-mask" @click.self="editingDevice = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('dev.editTitle') }}</h2><button class="sm" @click="editingDevice = null">{{ t('dev.close') }}</button></div>
        <div class="field"><label>{{ t('dev.code') }}</label><input :value="editingDevice.deviceCode" disabled /></div>
        <div class="field"><label>{{ t('dev.name') }}</label><input v-model="deviceEditForm.deviceName" /></div>
        <div class="field"><label>{{ t('dev.type') }}</label><select v-model="deviceEditForm.deviceType"><option value="LOCK">{{ t('dev.lock') }}</option><option value="METER">{{ t('dev.meter') }}</option><option value="ELEVATOR">{{ t('dev.elevator') }}</option><option value="GATE">{{ t('dev.gate') }}</option></select></div>
        <div class="field"><label>{{ t('dev.model') }}</label><input v-model="deviceEditForm.deviceModel" /></div>
        <div class="field"><label>{{ t('dev.install') }}</label><input v-model="deviceEditForm.installTime" type="datetime-local" /></div>
        <div class="field"><label>{{ t('dev.warranty') }}</label><input v-model="deviceEditForm.warrantyEnd" type="date" /></div>
        <div class="field"><label>{{ t('dev.remark') }}</label><input v-model="deviceEditForm.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveDeviceEdit">{{ t('dev.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
