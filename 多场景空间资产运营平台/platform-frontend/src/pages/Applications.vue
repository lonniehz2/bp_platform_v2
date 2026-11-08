<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const applications = ref([])
const persons = ref([])
const houses = ref([])
const waitlist = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ applicationNo: '', applicantPersonId: '', familySize: 1 })
const allocateForm = reactive({ waitlistId: '', houseId: '' })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red', SUBMITTED: 'orange' }[s] || '')
const money = (v) => Number(v || 0).toLocaleString('zh-CN')

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
    const [a, p, h, w] = await Promise.all([
      api.applications(project.value.id), api.persons(), api.houses(project.value.id), api.waitlist(project.value.id)
    ])
    applications.value = a; persons.value = p; houses.value = h; waitlist.value = w
    if (!form.applicantPersonId && p.length) form.applicantPersonId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.applicationNo.trim()) throw new Error('请填写申请编号')
    if (!form.applicantPersonId) throw new Error('请选择申请人')
    await api.createApplication({
      projectId: project.value.id,
      applicationNo: form.applicationNo.trim(),
      applicantPersonId: form.applicantPersonId,
      applicationType: 'PUBLIC_RENTAL',
      familySize: Number(form.familySize || 1)
    })
    form.applicationNo = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function submit(id) { await run(() => api.submitApplication(id)) }
async function approve(id) { await run(() => api.approveApplication(id, '资格通过')) }
async function wait(id) { await run(() => api.joinWaitlist(id)) }
async function allocate() {
  if (!allocateForm.waitlistId || !allocateForm.houseId) { error.value = '请选择轮候记录和房屋'; return }
  await run(() => api.allocate(allocateForm.waitlistId, allocateForm.houseId))
}

async function run(fn) {
  busy.value = true; error.value = ''
  try { await fn(); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head">
          <div><h2>保障房申请</h2><p>{{ project.orgName }} · 申请 → 审核 → 轮候 → 配租</p></div>
          <span class="pill">GUARANTEE</span>
        </div>
        <div class="row">
          <div class="field"><label>申请编号</label><input v-model="form.applicationNo" placeholder="如 APP2026001" /></div>
          <div class="field"><label>申请人</label>
            <select v-model="form.applicantPersonId">
              <option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}（{{ p.personCode }}）</option>
            </select>
          </div>
          <div class="field"><label>家庭人数</label><input v-model.number="form.familySize" type="number" min="1" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">创建申请</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>申请列表</h2><span class="small muted">审核通过后进入轮候</span></div>
        <div v-if="!applications.length" class="empty">暂无申请</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>申请编号</th><th>申请人</th><th>家庭人数</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="a in applications" :key="a.id">
                <td class="mono">{{ a.applicationNo }}</td>
                <td>{{ a.applicantName }}</td>
                <td>{{ a.familySize }}</td>
                <td><span class="badge" :class="statusClass(a.applicationStatus)">{{ a.applicationStatus }}</span></td>
                <td class="row">
                  <button class="sm" v-if="a.applicationStatus === 'DRAFT'" @click="submit(a.id)">提交</button>
                  <button class="sm" v-if="a.applicationStatus === 'SUBMITTED'" @click="approve(a.id)">审核通过</button>
                  <button class="sm" v-if="a.applicationStatus === 'APPROVED'" @click="wait(a.id)">进入轮候</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>轮候与配租</h2><span class="small muted">等待中的轮候记录可分配空置房屋</span></div>
        <div class="row" style="margin-bottom:12px">
          <div class="field"><label>轮候记录</label>
            <select v-model="allocateForm.waitlistId">
              <option value="">请选择</option>
              <option v-for="w in waitlist.filter(x => x.waitlistStatus === 'WAITING')" :key="w.id" :value="w.id">{{ w.queueNo }} · {{ w.applicantName }}</option>
            </select>
          </div>
          <div class="field"><label>房屋</label>
            <select v-model="allocateForm.houseId">
              <option value="">请选择</option>
              <option v-for="h in houses.filter(x => x.houseStatus === 'VACANT')" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option>
            </select>
          </div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="allocate">配租</button></div>
        </div>
        <div v-if="!waitlist.length" class="empty">暂无轮候</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>排队号</th><th>申请编号</th><th>申请人</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="w in waitlist" :key="w.id">
                <td>{{ w.queueNo }}</td><td class="mono">{{ w.applicationNo }}</td><td>{{ w.applicantName }}</td>
                <td><span class="badge" :class="w.waitlistStatus === 'ALLOCATED' ? 'green' : 'blue'">{{ w.waitlistStatus }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
