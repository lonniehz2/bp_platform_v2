<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const waitlist = ref([])
const houses = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ waitlistId: '', houseId: '' })
const waiting = computed(() => waitlist.value.filter(w => w.waitlistStatus === 'WAITING'))
const vacant = computed(() => houses.value.filter(h => h.houseStatus === 'VACANT'))
const allocated = computed(() => waitlist.value.filter(w => w.waitlistStatus === 'ALLOCATED'))

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
    const [w, h] = await Promise.all([api.waitlist(project.value.id), api.houses(project.value.id)])
    waitlist.value = w; houses.value = h
  } catch (e) { error.value = e.message }
}

async function allocate() {
  busy.value = true; error.value = ''
  try {
    if (!form.waitlistId || !form.houseId) throw new Error('请选择轮候记录和房屋')
    await api.allocate(form.waitlistId, form.houseId)
    form.waitlistId = ''; form.houseId = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid cards">
      <div class="card"><div class="label">待配租</div><div class="value">{{ waiting.length }}</div><div class="hint">轮候队列</div></div>
      <div class="card"><div class="label">已配租</div><div class="value">{{ allocated.length }}</div><div class="hint">历史配租</div></div>
      <div class="card"><div class="label">空置房源</div><div class="value">{{ vacant.length }}</div><div class="hint">可分配</div></div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><div><h2>配租摇号</h2><p>{{ project?.orgName || '未选择项目' }} · 轮候记录配租到空置房屋</p></div></div>
      <div class="row">
        <div class="field"><label>轮候记录</label><select v-model="form.waitlistId"><option value="">请选择</option><option v-for="w in waiting" :key="w.id" :value="w.id">{{ w.queueNo }} · {{ w.applicantName }}</option></select></div>
        <div class="field"><label>房屋</label><select v-model="form.houseId"><option value="">请选择</option><option v-for="h in vacant" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="allocate">确认配租</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>配租记录</h2><span class="small muted">{{ waitlist.length }} 条</span></div>
      <div v-if="!waitlist.length" class="empty">暂无记录</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>排队号</th><th>申请编号</th><th>申请人</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="w in waitlist" :key="w.id">
              <td>{{ w.queueNo }}</td><td class="mono">{{ w.applicationNo }}</td><td>{{ w.applicantName }}</td>
              <td><span class="badge" :class="w.waitlistStatus === 'ALLOCATED' ? 'green' : 'orange'">{{ w.waitlistStatus }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
