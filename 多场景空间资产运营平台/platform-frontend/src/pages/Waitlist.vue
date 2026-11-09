<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'

const project = ref(null)
const waitlist = ref([])
const houses = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ waitlistId: '', houseId: '' })
const waiting = computed(() => waitlist.value.filter(w => w.waitlistStatus === 'WAITING'))
const vacant = computed(() => houses.value.filter(h => h.houseStatus === 'VACANT'))

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
    <div class="panel">
      <div class="panel-head"><div><h2>轮候管理</h2><p>{{ project?.orgName || '未选择项目' }} · 轮候队列与排位</p></div><span class="badge blue">{{ waiting.length }} 户等待</span></div>
      <div class="row">
        <div class="field"><label>轮候记录</label><SearchSelect v-model="form.waitlistId" :options="waiting" label-key="queueNo" sublabel-key="applicantName" value-key="id" placeholder="搜索轮候记录" /></div>
        <div class="field"><label>空置房屋</label><SearchSelect v-model="form.houseId" :options="vacant" label-key="houseCode" sublabel-key="houseName" value-key="id" placeholder="搜索空置房屋" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="allocate">配租</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>轮候队列</h2><span class="small muted">{{ waitlist.length }} 条</span></div>
      <div v-if="!waitlist.length" class="empty">暂无轮候</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>排队号</th><th>申请编号</th><th>申请人</th><th>状态</th><th>登记时间</th></tr></thead>
          <tbody>
            <tr v-for="w in waitlist" :key="w.id">
              <td class="mono">{{ w.queueNo }}</td><td class="mono">{{ w.applicationNo }}</td><td>{{ w.applicantName }}</td>
              <td><span class="badge" :class="w.waitlistStatus === 'ALLOCATED' ? 'green' : 'blue'">{{ w.waitlistStatus }}</span></td>
              <td class="small">{{ w.createTime }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
