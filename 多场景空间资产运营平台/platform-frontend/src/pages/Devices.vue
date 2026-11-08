<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'
import Pager from '../components/Pager.vue'

const project = ref(null)
const devices = ref([])
const page = ref(1)
const persons = ref([])
const spaces = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ deviceCode: '', deviceName: '', deviceType: 'LOCK', spaceId: '' })
const grantForm = reactive({ personId: '', targetId: '', validStart: '2026-11-08', validEnd: '2027-11-07' })
const grants = ref([])

const money = (v) => Number(v || 0).toLocaleString('zh-CN')
const pagedDevices = computed(() => devices.value.slice((page.value - 1) * 10, page.value * 10))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  if (chosen) return chosen
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
      deviceType: form.deviceType, assetStatus: 'ACTIVE', businessStatus: 'IN_USE'
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
          <div class="field"><label>绑定空间</label>
            <select v-model="form.spaceId"><option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.spaceName }}（{{ s.spaceType }}）</option></select>
          </div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('device')" class="primary" :disabled="busy" @click="createDevice">新增设备</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>设备列表</h2><span class="small muted">{{ devices.length }} 台设备</span></div>
        <div v-if="!devices.length" class="empty">暂无设备</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>设备编码</th><th>名称</th><th>类型</th><th>绑定空间</th><th>资产状态</th><th>业务状态</th></tr></thead>
            <tbody>
              <tr v-for="d in pagedDevices" :key="d.id">
                <td class="mono">{{ d.deviceCode }}</td><td>{{ d.deviceName }}</td><td>{{ d.deviceType }}</td>
                <td>{{ d.spaceName || '-' }}</td><td><span class="badge green">{{ d.assetStatus }}</span></td><td>{{ d.businessStatus }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pager :total="devices.length" :page="page" @update:page="page = $event" />
      </div>

      <div class="panel">
        <div class="panel-head"><h2>人员授权</h2><span class="small muted">授权到空间，钥匙包按人员聚合</span></div>
        <div class="row">
          <div class="field"><label>人员</label>
            <select v-model="grantForm.personId" @change="loadGrants"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select>
          </div>
          <div class="field"><label>授权空间</label>
            <select v-model="grantForm.targetId"><option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.spaceName }}</option></select>
          </div>
          <div class="field"><label>开始日期</label><input v-model="grantForm.validStart" type="date" /></div>
          <div class="field"><label>结束日期</label><input v-model="grantForm.validEnd" type="date" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="createGrant">新增授权</button></div>
        </div>
        <div v-if="grants.length" class="table-wrap" style="margin-top:12px">
          <table>
            <thead><tr><th>类型</th><th>授权对象</th><th>级别</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="g in grants" :key="g.id">
                <td>{{ g.targetType }}</td><td class="mono">{{ g.targetId }}</td><td>{{ g.grantLevel }}</td>
                <td class="small">{{ g.validStart }} ~ {{ g.validEnd || '长期' }}</td>
                <td><span class="badge" :class="g.grantStatus === 'ACTIVE' ? 'green' : 'orange'">{{ g.grantStatus }}</span></td>
                <td><button v-if="g.grantStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="revokeGrant(g)">撤销</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty">暂无授权</div>
      </div>
    </template>
  </div>
</template>
