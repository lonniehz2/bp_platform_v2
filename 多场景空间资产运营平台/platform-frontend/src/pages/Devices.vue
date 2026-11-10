<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import TreeSelect from '../components/TreeSelect.vue'
import { confirmAction } from '../confirm'
import { can, canAction } from '../permissions'
import DataTable from '../components/DataTable.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'

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
  { key: 'deviceCode', title: '设备编码', width: '150px' },
  { key: 'deviceName', title: '名称', width: '130px' },
  { key: 'deviceType', title: '类型', width: '80px' },
  { key: 'deviceModel', title: '型号', width: '110px' },
  { key: 'deviceMac', title: '物理MAC', width: '150px' },
  { key: 'spaceName', title: '绑定空间', width: '140px' },
  { key: 'installStatus', title: '安装状态', width: '90px' },
  { key: 'warrantyEnd', title: '保修到期', width: '110px' },
  { key: 'assetStatus', title: '资产状态', width: '90px' },
  { key: 'businessStatus', title: '业务状态', width: '90px' },
  { key: 'actions', title: '操作', width: '220px' }
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
    if (!form.deviceCode.trim()) throw new Error('请填写设备编码')
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
    alert('授权已创建')
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function revokeGrant(g) {
  busy.value = true; error.value = ''
  try { await api.revokeGrant(g.id, '页面撤销'); await loadGrants() } catch (e) { error.value = e.message } finally { busy.value = false }
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
    if (!deviceEditForm.deviceName.trim()) throw new Error('设备名称不能为空')
    await api.updateDevice(editingDevice.value.id, { ...deviceEditForm })
    editingDevice.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function archiveDevice(d) {
  if (!await confirmAction({ title: '报废设备', message: `确认报废设备 ${d.deviceCode}？报废后不再显示。`, confirmText: '报废', danger: true })) return
  busy.value = true; error.value = ''
  try { await api.archiveDevice(d.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function repairDevice(d) {
  if (!await confirmAction({ title: '设备报修', message: `确认将设备 ${d.deviceCode} 标记为报修？`, confirmText: '报修', danger: true })) return
  busy.value = true; error.value = ''
  try { await api.repairDevice(d.id, { reason: '页面报修' }); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function enableDevice(d) {
  if (!await confirmAction({ title: '启用设备', message: `确认启用设备 ${d.deviceCode}？`, confirmText: '启用' })) return
  busy.value = true; error.value = ''
  try { await api.enableDevice(d.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>设备业务资产</h2><p>{{ project.orgName }} · 业务台账，不涉及 IOT 控制</p></div><span class="pill">DEVICE</span></div>
        <div class="row">
          <div class="field"><label>设备编码</label><input v-model="form.deviceCode" placeholder="如 LOCK-001" /></div>
          <div class="field"><label>设备名称</label><input v-model="form.deviceName" placeholder="101门锁" /></div>
          <div class="field"><label>设备类型</label>
            <select v-model="form.deviceType"><option value="LOCK">门锁</option><option value="METER">水电表</option><option value="ELEVATOR">电梯</option><option value="GATE">门禁</option></select>
          </div>
          <div class="field"><label>设备型号</label><input v-model="form.deviceModel" /></div>
          <div class="field"><label>安装时间</label><input v-model="form.installTime" type="datetime-local" /></div>
          <div class="field"><label>保修到期</label><input v-model="form.warrantyEnd" type="date" /></div>
          <div class="field"><label>绑定空间</label>
            <TreeSelect v-model="form.spaceId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" placeholder="选择绑定空间" />
          </div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="canAction('device:create', 'device')" class="primary" :disabled="busy" @click="createDevice">新增设备</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>设备列表</h2><span class="small muted">{{ devices.length }} 台设备</span></div>
        <div class="row" style="margin-bottom:8px">
          <input v-model="deviceQuery" placeholder="搜索设备编码/名称/MAC/空间" style="max-width:320px" @input="page = 1" />
        </div>
        <DataTable :rows="pagedDevices" :columns="deviceColumns" :page="page" :page-size="10" :total="filteredDevices.length" empty-text="暂无设备" @update:page="page = $event">
          <template #cell-assetStatus="{ row }"><span class="badge green">{{ row.assetStatus }}</span></template>
          <template #cell-actions="{ row }">
            <button class="sm" @click="openDeviceEdit(row)">编辑</button>
            <button class="sm" @click="detailDevice = row">关联</button>
            <button v-if="canAction('device:archive', 'device')" class="sm danger" :disabled="busy" @click="archiveDevice(row)">报废</button>
            <button v-if="canAction('device:repair', 'device') && row.businessStatus !== 'FAULT'" class="sm" :disabled="busy" @click="repairDevice(row)">报修</button>
            <button v-if="canAction('device:enable', 'device') && ['FAULT','DISABLED'].includes(row.businessStatus)" class="sm primary" :disabled="busy" @click="enableDevice(row)">启用</button>
          </template>
        </DataTable>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>人员授权</h2><span class="small muted">授权到空间，钥匙包按人员聚合</span></div>
        <div class="row">
          <div class="field"><label>人员</label>
            <SearchSelect v-model="grantForm.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" placeholder="搜索人员" @change="loadGrants" />
          </div>
          <div class="field"><label>授权空间</label>
            <TreeSelect v-model="grantForm.targetId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" placeholder="选择授权空间" />
          </div>
          <div class="field"><label>开始日期</label><input v-model="grantForm.validStart" type="date" /></div>
          <div class="field"><label>结束日期</label><input v-model="grantForm.validEnd" type="date" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="canAction('device:grant', 'device')" class="primary" :disabled="busy" @click="createGrant">新增授权</button></div>
        </div>
        <div v-if="grants.length" class="table-wrap" style="margin-top:12px">
          <table>
            <thead><tr><th>类型</th><th>授权对象</th><th>级别</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="g in grants" :key="g.id">
                <td>{{ g.targetType }}</td><td class="mono">{{ g.targetId }}</td><td>{{ g.grantLevel }}</td>
                <td class="small">{{ g.validStart }} ~ {{ g.validEnd || '长期' }}</td>
                <td><span class="badge" :class="g.grantStatus === 'ACTIVE' ? 'green' : 'orange'">{{ g.grantStatus }}</span></td>
                <td><button v-if="canAction('device:grant', 'device') && g.grantStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="revokeGrant(g)">撤销</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty">暂无授权</div>
      </div>
    </template>

    <div v-if="detailDevice" class="modal-mask" @click.self="detailDevice = null">
      <div class="modal" style="max-width:720px">
        <div class="panel-head"><div><h2>{{ detailDevice.deviceName }}</h2><p class="small muted">{{ detailDevice.deviceCode }}</p></div><button class="sm" @click="detailDevice = null">关闭</button></div>
        <EntityDetailTabs type="DEVICE" :entity-id="detailDevice.id" />
      </div>
    </div>

    <div v-if="editingDevice" class="modal-mask" @click.self="editingDevice = null">
      <div class="modal">
        <div class="panel-head"><h2>编辑设备</h2><button class="sm" @click="editingDevice = null">关闭</button></div>
        <div class="field"><label>设备编码</label><input :value="editingDevice.deviceCode" disabled /></div>
        <div class="field"><label>设备名称</label><input v-model="deviceEditForm.deviceName" /></div>
        <div class="field"><label>设备类型</label><select v-model="deviceEditForm.deviceType"><option value="LOCK">门锁</option><option value="METER">水电表</option><option value="ELEVATOR">电梯</option><option value="GATE">门禁</option></select></div>
        <div class="field"><label>型号</label><input v-model="deviceEditForm.deviceModel" /></div>
        <div class="field"><label>安装时间</label><input v-model="deviceEditForm.installTime" type="datetime-local" /></div>
        <div class="field"><label>保修到期</label><input v-model="deviceEditForm.warrantyEnd" type="date" /></div>
        <div class="field"><label>备注</label><input v-model="deviceEditForm.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveDeviceEdit">保存</button></div>
      </div>
    </div>
  </div>
</template>
