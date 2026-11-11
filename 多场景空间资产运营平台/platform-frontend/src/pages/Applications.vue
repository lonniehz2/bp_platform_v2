<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can, canAction } from '../permissions'
import SearchSelect from '../components/SearchSelect.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import { confirmAction } from '../confirm'

const project = ref(null)
const applications = ref([])
const persons = ref([])
const houses = ref([])
const waitlist = ref([])
const detailApp = ref(null)
const createOpen = ref(false)
const allocateOpen = ref(false)
const error = ref('')
const busy = ref(false)
const form = reactive({ applicationNo: '', applicantPersonId: '', familySize: 1, applicationType: 'PUBLIC_RENTAL', contactPhone: '', incomeLevel: 'LOW', housingStatus: 'NO_HOUSE', urgency: 'NORMAL', remark: '', guaranteeType: 'PUBLIC_RENTAL', familyType: 'SINGLE', subsidyStatus: 'NONE', archiveNo: '' })
const allocateForm = reactive({ waitlistId: '', houseId: '' })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red', SUBMITTED: 'orange' }[s] || '')
const money = (v) => Number(v || 0).toLocaleString('zh-CN')
const incomeLabel = (v) => ({ LOW: '低收入', LOWER_MIDDLE: '中低收入', MIDDLE: '中等收入' }[v] || v || '-')
const housingLabel = (v) => ({ NO_HOUSE: '无房', RENTING: '租房', WITH_FAMILY: '与家人同住' }[v] || v || '-')
const urgencyLabel = (v) => ({ NORMAL: '普通', URGENT: '紧急' }[v] || v || '-')

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
    const [a, p, h, w] = await Promise.all([
      api.applications(project.value.id), api.persons().catch(() => []),
      api.houses(project.value.id).catch(() => []), api.waitlist(project.value.id).catch(() => [])
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
    if (form.contactPhone && !/^1\d{10}$/.test(form.contactPhone)) throw new Error('联系电话需为 11 位手机号')
    if (Number(form.familySize) < 1 || Number(form.familySize) > 20) throw new Error('家庭人数需在 1-20 之间')
    await api.createApplication({
      projectId: project.value.id,
      applicationNo: form.applicationNo.trim(),
      applicantPersonId: form.applicantPersonId,
      applicationType: form.applicationType,
      familySize: Number(form.familySize || 1), contactPhone: form.contactPhone,
      incomeLevel: form.incomeLevel, housingStatus: form.housingStatus,
      urgency: form.urgency, remark: form.remark,
      guaranteeType: form.guaranteeType, familyType: form.familyType,
      subsidyStatus: form.subsidyStatus, archiveNo: form.archiveNo
    })
    form.applicationNo = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function submit(id) { await run(() => api.submitApplication(id)) }
async function approve(id) { await run(() => api.approveApplication(id, '资格通过')) }
async function wait(id) { await run(() => api.joinWaitlist(id)) }
async function reject(id) { const comment = window.prompt('驳回原因') || '资料不齐'; await run(() => api.rejectApplication(id, comment)) }
async function returnForSupplement(id) { const comment = window.prompt('退回补充原因') || '请补充资料'; await run(() => api.returnApplication(id, comment)) }
async function resubmit(id) { await run(() => api.resubmitApplication(id)) }

async function discardApplication(a) {
  if (!await confirmAction({ title: '作废申请', message: `确认作废申请 ${a.applicationNo}？`, confirmText: '作废', danger: true })) return
  await run(() => api.discardApplication(a.id))
}

async function closeApplication(a) {
  if (!await confirmAction({ title: '关闭申请', message: `确认关闭申请 ${a.applicationNo}？`, confirmText: '关闭', danger: true })) return
  await run(() => api.closeApplication(a.id))
}

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
          <div class="row">
            <button v-if="canAction('application:create', 'application')" class="primary" @click="createOpen = true">新建申请</button>
            <button v-if="canAction('allocation:create', 'application')" class="sm" @click="allocateOpen = true">配租</button>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>申请列表</h2><span class="small muted">审核通过后进入轮候</span></div>
        <div v-if="!applications.length" class="empty">暂无申请</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>申请编号</th><th>申请人</th><th>保障类型</th><th>家庭结构</th><th>档案编号</th><th>家庭人数</th><th>收入水平</th><th>住房情况</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="a in applications" :key="a.id">
                <td class="mono">{{ a.applicationNo }}</td>
                <td>{{ a.applicantName }}</td>
                <td>{{ a.guaranteeType || '-' }}</td><td>{{ a.familyType || '-' }}</td><td>{{ a.archiveNo || '-' }}</td>
                <td>{{ a.familySize }}</td><td>{{ incomeLabel(a.incomeLevel) }}</td><td>{{ housingLabel(a.housingStatus) }}</td>
                <td><span class="badge" :class="statusClass(a.applicationStatus)">{{ a.applicationStatus }}</span></td>
                <td class="row">
                  <button class="sm" @click="detailApp = a">详情</button>
                  <button class="sm" v-if="canAction('application:submit', 'application') && a.applicationStatus === 'DRAFT'" :disabled="busy" @click="submit(a.id)">提交</button>
                  <button class="sm danger" v-if="canAction('application:discard', 'application') && a.applicationStatus === 'DRAFT'" :disabled="busy" @click="discardApplication(a)">作废</button>
                  <button class="sm" v-if="canAction('application:approve', 'application') && a.applicationStatus === 'SUBMITTED'" :disabled="busy" @click="approve(a.id)">审核通过</button>
                  <button class="sm danger" v-if="canAction('application:reject', 'application') && a.applicationStatus === 'SUBMITTED'" :disabled="busy" @click="reject(a.id)">驳回</button>
                  <button class="sm" v-if="canAction('application:return', 'application') && a.applicationStatus === 'SUBMITTED'" :disabled="busy" @click="returnForSupplement(a.id)">退回补充</button>
                  <button class="sm" v-if="canAction('application:resubmit', 'application') && a.applicationStatus === 'RETURNED'" :disabled="busy" @click="resubmit(a.id)">重新提交</button>
                  <button class="sm" v-if="canAction('application:waitlist', 'application') && a.applicationStatus === 'APPROVED'" :disabled="busy" @click="wait(a.id)">进入轮候</button>
                  <button class="sm" v-if="canAction('application:close', 'application') && ['CONTRACTED','REJECTED'].includes(a.applicationStatus)" :disabled="busy" @click="closeApplication(a)">关闭</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>轮候与配租</h2><span class="small muted">等待中的轮候记录可分配空置房屋</span></div>
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

    <div v-if="detailApp" class="modal-mask" @click.self="detailApp = null">
      <div class="modal" style="max-width:720px">
        <div class="panel-head"><h2>申请详情</h2><button class="sm" @click="detailApp = null">关闭</button></div>
        <div class="row" style="justify-content:flex-end;margin-bottom:8px"><RouterLink class="sm" :to="`/guarantee/detail/APPLICATION/${detailApp.id}`">打开 Tab 详情页</RouterLink></div>
        <EntityDetailTabs type="APPLICATION" :entity-id="detailApp.id" />
        <div class="row">
          <div class="field"><label>申请编号</label><div class="mono">{{ detailApp.applicationNo }}</div></div>
          <div class="field"><label>申请人</label><div>{{ detailApp.applicantName }}</div></div>
          <div class="field"><label>状态</label><span class="badge" :class="statusClass(detailApp.applicationStatus)">{{ detailApp.applicationStatus }}</span></div>
          <div class="field"><label>保障类型</label><div>{{ detailApp.guaranteeType || '-' }}</div></div>
          <div class="field"><label>家庭结构</label><div>{{ detailApp.familyType || '-' }}</div></div>
          <div class="field"><label>家庭人数</label><div>{{ detailApp.familySize }}</div></div>
          <div class="field"><label>收入水平</label><div>{{ incomeLabel(detailApp.incomeLevel) }}</div></div>
          <div class="field"><label>住房情况</label><div>{{ housingLabel(detailApp.housingStatus) }}</div></div>
          <div class="field"><label>档案编号</label><div>{{ detailApp.archiveNo || '-' }}</div></div>
        </div>
      </div>
    </div>

    <div v-if="createOpen" class="modal-mask" @click.self="createOpen = false">
      <div class="modal" style="max-width:860px">
        <div class="panel-head"><h2>新建申请</h2><button class="sm" @click="createOpen = false">关闭</button></div>
        <div class="row">
          <div class="field"><label>申请编号</label><input v-model="form.applicationNo" placeholder="如 APP2026001" /></div>
          <div class="field"><label>申请人</label><SearchSelect v-model="form.applicantPersonId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" placeholder="搜索姓名/编码" /></div>
          <div class="field"><label>申请类型</label><select v-model="form.applicationType"><option value="PUBLIC_RENTAL">公共租赁</option><option value="AFFORDABLE_RENTAL">保障性租赁</option><option value="TALENT_APARTMENT">人才公寓</option><option value="DORMITORY">宿舍</option></select></div>
          <div class="field"><label>家庭人数</label><input v-model.number="form.familySize" type="number" min="1" /></div>
          <div class="field"><label>联系电话</label><input v-model="form.contactPhone" /></div>
          <div class="field"><label>收入水平</label><select v-model="form.incomeLevel"><option value="LOW">低收入</option><option value="LOWER_MIDDLE">中低收入</option><option value="MIDDLE">中等收入</option></select></div>
          <div class="field"><label>住房情况</label><select v-model="form.housingStatus"><option value="NO_HOUSE">无房</option><option value="RENTING">租房</option><option value="WITH_FAMILY">与家人同住</option></select></div>
          <div class="field"><label>紧急程度</label><select v-model="form.urgency"><option value="NORMAL">普通</option><option value="URGENT">紧急</option></select></div>
          <div class="field"><label>保障类型</label><select v-model="form.guaranteeType"><option value="PUBLIC_RENTAL">公共租赁</option><option value="LOW_RENT">廉租住房</option><option value="SUBSIDY">租赁补贴</option></select></div>
          <div class="field"><label>家庭结构</label><select v-model="form.familyType"><option value="SINGLE">单身</option><option value="COUPLE">夫妻</option><option value="WITH_CHILDREN">有子女家庭</option><option value="ELDERLY">老年家庭</option></select></div>
          <div class="field"><label>补贴状态</label><select v-model="form.subsidyStatus"><option value="NONE">无</option><option value="APPLYING">申请中</option><option value="ACTIVE">已享受</option></select></div>
          <div class="field"><label>档案编号</label><input v-model="form.archiveNo" /></div>
          <div class="field" style="flex:2"><label>备注</label><input v-model="form.remark" /></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="create">创建申请</button></div>
      </div>
    </div>

    <div v-if="allocateOpen" class="modal-mask" @click.self="allocateOpen = false">
      <div class="modal" style="max-width:620px">
        <div class="panel-head"><h2>配租</h2><button class="sm" @click="allocateOpen = false">关闭</button></div>
        <div class="row">
          <div class="field"><label>轮候记录</label><SearchSelect v-model="allocateForm.waitlistId" :options="waitlist.filter(x => x.waitlistStatus === 'WAITING')" label-key="queueNo" sublabel-key="applicantName" value-key="id" placeholder="搜索轮候记录" /></div>
          <div class="field"><label>房屋</label><SearchSelect v-model="allocateForm.houseId" :options="houses.filter(x => x.houseStatus === 'VACANT')" label-key="houseCode" sublabel-key="houseName" value-key="id" placeholder="搜索空置房屋" /></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="allocate(); allocateOpen = false">确认配租</button></div>
      </div>
    </div>
  </div>
</template>
