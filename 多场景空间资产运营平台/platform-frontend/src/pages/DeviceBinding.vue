<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const devices = ref([])
const spaces = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ deviceId: '', spaceId: '' })
const unbound = computed(() => devices.value.filter(d => !d.spaceId))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const [d, s] = await Promise.all([api.devices(project.value.id), api.spaces(project.value.id)])
    devices.value = d; spaces.value = s
    if (!form.deviceId && d.length) form.deviceId = d[0].id
    if (!form.spaceId && s.length) form.spaceId = s[0].id
  } catch (e) { error.value = e.message }
}

async function bind() {
  busy.value = true; error.value = ''
  try {
    if (!form.deviceId || !form.spaceId) throw new Error('请选择设备和空间')
    await api.bindDevice(form.deviceId, form.spaceId)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function unbind(d) {
  busy.value = true; error.value = ''
  try { await api.bindDevice(d.id, null); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>设备绑定</h2><p>{{ project?.orgName || '未选择项目' }} · 设备与空间的绑定/解绑</p></div><span class="badge blue">{{ unbound.length }} 台未绑定</span></div>
      <div class="row">
        <div class="field"><label>设备</label><select v-model="form.deviceId"><option v-for="d in devices" :key="d.id" :value="d.id">{{ d.deviceCode }} · {{ d.deviceName }}</option></select></div>
        <div class="field"><label>绑定空间</label><select v-model="form.spaceId"><option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.spaceName }}（{{ s.spaceType }}）</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('device')" class="primary" :disabled="busy" @click="bind">绑定</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>设备绑定列表</h2><span class="small muted">{{ devices.length }} 台设备</span></div>
      <div v-if="!devices.length" class="empty">暂无设备</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>设备编码</th><th>名称</th><th>类型</th><th>绑定空间</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="d in devices" :key="d.id">
              <td class="mono">{{ d.deviceCode }}</td><td>{{ d.deviceName }}</td><td>{{ d.deviceType }}</td>
              <td>{{ d.spaceName || '未绑定' }}</td>
              <td><span class="badge" :class="d.spaceId ? 'green' : 'orange'">{{ d.spaceId ? 'BOUND' : 'UNBOUND' }}</span></td>
              <td><button v-if="can('device') && d.spaceId" class="sm" :disabled="busy" @click="unbind(d)">解绑</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
