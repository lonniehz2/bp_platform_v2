<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { contractStatusLabel, contractStatusTone } from '../contractStatus'
import { api } from '../api'
import { can } from '../permissions'
import DataTable from '../components/DataTable.vue'
import SearchSelect from '../components/SearchSelect.vue'
import { confirmAction } from '../confirm'

const persons = ref([])
const grants = ref([])
const relations = ref([])
const projects = ref([])
const houses = ref([])
const project = ref(null)
const selected = ref(null)
const contractRelations = ref(null)
const error = ref('')
const busy = ref(false)
const page = ref(1)
const relationLabels = { TENANT: '承租人', FAMILY: '家庭成员', COHABITANT: '同住人', OWNER: '产权人', SPOUSE: '配偶', CHILD: '子女', PARENT: '父母', OTHER: '其他' }
const relationLabel = (v) => relationLabels[v] || v || '-'
const relationStatusLabels = { ACTIVE: '有效', INACTIVE: '已结束', ENDED: '已结束' }
const relationStatusLabel = (v) => relationStatusLabels[v] || v || '-'
const route = useRoute()
const router = useRouter()
const personQuery = ref('')
const relForm = reactive({ targetType: 'HOUSE', targetId: '', relationType: 'TENANT', startDate: '', endDate: '' })
const form = reactive({ personCode: '', personName: '', phone: '', idCardMask: '', personType: 'GUARANTEE_TENANT', gender: '', birthDate: '', address: '', employer: '', emergencyContact: '', remark: '' })
const filteredPersons = computed(() => {
  const q = personQuery.value.trim().toLowerCase()
  if (!q) return persons.value
  return persons.value.filter(p => (String(p.personCode) + ' ' + String(p.personName || '') + ' ' + String(p.phone || '')).toLowerCase().includes(q))
})
const paged = computed(() => filteredPersons.value.slice((page.value - 1) * 10, page.value * 10))
const editingPerson = ref(null)
const personEditForm = reactive({ personCode: '', personName: '', phone: '', idCardMask: '', personType: 'GUARANTEE_TENANT', gender: '', birthDate: '', address: '', employer: '', emergencyContact: '', remark: '' })
const personColumns = [
  { key: 'personCode', title: '人员编码', width: '140px' },
  { key: 'personName', title: '姓名', width: '110px' },
  { key: 'phone', title: '手机号', width: '130px' },
  { key: 'gender', title: '性别', width: '70px' },
  { key: 'personType', title: '类型', width: '120px' },
  { key: 'status', title: '状态', width: '80px' },
  { key: 'actions', title: '操作', width: '200px' }
]

async function load() {
  error.value = ''
  try {
    const all = await api.projects()
    projects.value = all
    const saved = String(localStorage.getItem('platformProjectId') || '')
    project.value = all.find(p => String(p.id) === saved) || all[0] || null
    persons.value = await api.persons()
    houses.value = project.value ? await api.houses(project.value.id) : []
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.personCode.trim() || !form.personName.trim()) throw new Error('请填写人员编码和姓名')
    if (form.phone && !/^1\d{10}$/.test(form.phone)) throw new Error('手机号需为 11 位号码')
    if (form.birthDate && new Date(form.birthDate) > new Date()) throw new Error('出生日期不能晚于今天')
    await api.createPerson({
      personCode: form.personCode.trim(), personName: form.personName.trim(),
      phone: form.phone, idCardMask: form.idCardMask, personType: form.personType,
      gender: form.gender, birthDate: form.birthDate || null, address: form.address,
      employer: form.employer, emergencyContact: form.emergencyContact, remark: form.remark
    })
    form.personCode = ''; form.personName = ''; form.phone = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function selectPerson(p) {
  selected.value = p
  contractRelations.value = null
  try {
    const [g, r, cr] = await Promise.all([
      api.keyring(p.id),
      api.relations(p.id),
      api.personContractRelations(p.id).catch(() => null)
    ])
    grants.value = g
    relations.value = r
    contractRelations.value = cr
  } catch {
    grants.value = []
    relations.value = []
    contractRelations.value = null
  }
  await nextTick()
  document.getElementById('person-detail')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}


async function removeRelation(r) {
  if (!selected.value) return
  if (!await confirmAction({ title: '移除人员关系', message: `确认移除 ${r.targetName || r.relationType} 关系？`, confirmText: '移除', danger: true })) return
  busy.value = true; error.value = ''
  try { await api.removePersonRelation(selected.value.id, r.id); relations.value = await api.relations(selected.value.id) } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function addRelation() {
  if (!selected.value || !relForm.targetId) { error.value = '请选择关联对象'; return }
  busy.value = true; error.value = ''
  try {
    await api.createRelation(selected.value.id, {
      projectId: project.value?.id, targetType: relForm.targetType, targetId: relForm.targetId,
      relationType: relForm.relationType, startDate: relForm.startDate || null, endDate: relForm.endDate || null
    })
    relations.value = await api.relations(selected.value.id)
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


function openPersonEdit(p) {
  editingPerson.value = p
  Object.assign(personEditForm, {
    personCode: p.personCode || '', personName: p.personName || '', phone: p.phone || '',
    idCardMask: p.idCardMask || '', personType: p.personType || 'GUARANTEE_TENANT', gender: p.gender || '',
    birthDate: p.birthDate || '', address: p.address || '', employer: p.employer || '',
    emergencyContact: p.emergencyContact || '', remark: p.remark || ''
  })
}


async function archivePerson(p) {
  if (!await confirmAction({ title: '归档人员', message: `确认归档 ${p.personName}？存在合同时会被拒绝。`, confirmText: '归档', danger: true })) return
  busy.value = true; error.value = ''
  try { await api.archivePerson(p.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function savePersonEdit() {
  busy.value = true; error.value = ''
  try {
    if (!personEditForm.personName.trim()) throw new Error('姓名不能为空')
    await api.updatePerson(editingPerson.value.id, { ...personEditForm })
    editingPerson.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function togglePersonStatus(p) {
  const next = p.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  if (!await confirmAction({ title: '变更人员状态', message: `确认将 ${p.personName} 设为 ${next}？`, confirmText: '确认' })) return
  busy.value = true; error.value = ''
  try { await api.updatePersonStatus(p.id, next); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(async () => {
  await load()
  const id = String(route.query.id || '')
  const found = persons.value.find(p => String(p.id) === id)
  if (found) selectPerson(found)
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>人员档案</h2><p>保障对象、家庭成员、承租人、同住人、访客、服务人员</p></div><div class="row"><span class="badge blue">{{ persons.length }} 人</span><RouterLink class="sm" to="/guarantee/imports">批量导入</RouterLink></div></div>
      <div class="row">
        <div class="field"><label>人员编码</label><input v-model="form.personCode" placeholder="如 P0001" /></div>
        <div class="field"><label>姓名</label><input v-model="form.personName" /></div>
        <div class="field"><label>手机号</label><input v-model="form.phone" /></div>
        <div class="field"><label>证件号掩码</label><input v-model="form.idCardMask" placeholder="330***********1234" /></div>
        <div class="field"><label>性别</label><select v-model="form.gender"><option value="">未填写</option><option value="MALE">男</option><option value="FEMALE">女</option></select></div>
        <div class="field"><label>出生日期</label><input v-model="form.birthDate" type="date" /></div>
        <div class="field"><label>人员类型</label>
          <select v-model="form.personType">
            <option value="GUARANTEE_TENANT">保障对象</option>
            <option value="FAMILY">家庭成员</option>
            <option value="TENANT">承租人</option>
            <option value="COHABITANT">同住人</option>
            <option value="VISITOR">访客</option>
            <option value="STAFF">服务人员</option>
          </select>
        </div>
        <div class="field" style="flex:2"><label>住址</label><input v-model="form.address" /></div>
        <div class="field"><label>工作单位</label><input v-model="form.employer" /></div>
        <div class="field"><label>紧急联系人</label><input v-model="form.emergencyContact" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('person')" class="primary" :disabled="busy" @click="create">新增人员</button></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns: 1.3fr .7fr">
      <div class="panel">
        <div class="panel-head"><h2>人员列表</h2><span class="small muted">点击查看钥匙包</span></div>
        <div class="row" style="margin-bottom:8px">
          <input v-model="personQuery" placeholder="搜索姓名/编码/手机号" style="max-width:280px" @input="page = 1" />
        </div>
        <div v-if="selected" class="alert">当前人员：<strong>{{ selected.personName }}</strong>（{{ selected.personCode }}）<span v-if="contractRelations" class="small muted"> · 承租人合同 {{ contractRelations.tenantContracts?.length || 0 }} · 同住合同 {{ contractRelations.cohabitantContracts?.length || 0 }}</span></div>
        <DataTable :rows="paged" :columns="personColumns" :page="page" :page-size="10" :total="filteredPersons.length" empty-text="暂无人员" @update:page="page = $event" @row-click="selectPerson">
          <template #cell-gender="{ row }">{{ row.gender === 'MALE' ? '男' : row.gender === 'FEMALE' ? '女' : '-' }}</template>
          <template #cell-status="{ row }"><span class="badge" :class="row.status === 'ENABLED' ? 'green' : 'orange'">{{ row.status }}</span></template>
          <template #cell-actions="{ row }">
            <button class="sm" @click.stop="openPersonEdit(row)">编辑</button>
            <button class="sm" :class="row.status === 'ENABLED' ? 'danger' : ''" :disabled="busy" @click.stop="togglePersonStatus(row)">{{ row.status === 'ENABLED' ? '停用' : '启用' }}</button>
            <button class="sm danger" :disabled="busy" @click.stop="archivePerson(row)">归档</button>
          </template>
        </DataTable>
      </div>

      <div v-if="selected" id="person-detail" class="panel">
        <div class="panel-head"><div><h2>合同关系</h2><p>{{ selected.personName }} · 承租人 / 同住人</p></div></div>
        <div v-if="!contractRelations" class="empty">暂无合同关系或无查看权限</div>
        <template v-else>
          <div class="section-title">当前承租人合同</div>
          <div v-if="!contractRelations.tenantContracts?.length" class="empty">暂无承租人合同</div>
          <div v-for="c in contractRelations.tenantContracts" :key="'t'+c.id" class="entity-row">
            <div><strong>{{ c.contractNo }}</strong><div class="small muted">{{ c.houseName || '房屋不可见' }} · {{ c.startDate || '' }} ~ {{ c.endDate || '' }}</div></div>
            <div class="row"><span class="badge" :class="c.accessible ? contractStatusTone(c.contractStatus) : 'orange'">{{ c.accessible ? contractStatusLabel(c.contractStatus) : '无权限' }}</span><button v-if="c.accessible" class="sm" @click="router.push(c.route)">查看合同</button></div>
          </div>
          <div class="section-title">作为同住人的合同</div>
          <div v-if="!contractRelations.cohabitantContracts?.length" class="empty">暂无同住合同</div>
          <div v-for="c in contractRelations.cohabitantContracts" :key="'c'+c.id" class="entity-row">
            <div><strong>{{ c.contractNo }}</strong><div class="small muted">主承租人：{{ c.mainTenantName || '-' }} · {{ c.startDate || '' }} ~ {{ c.endDate || '' }}</div></div>
            <div class="row"><span class="badge" :class="c.accessible ? contractStatusTone(c.contractStatus) : 'orange'">{{ c.accessible ? contractStatusLabel(c.contractStatus) : '无权限' }}</span><button v-if="c.accessible" class="sm" @click="router.push(c.route)">查看合同</button></div>
          </div>
          <div class="section-title">同住人</div>
          <div v-if="!contractRelations.cohabitants?.length" class="empty">暂无同住人</div>
          <div v-for="c in contractRelations.cohabitants" :key="c.contractId + '-' + c.personId" class="entity-row">
            <span>{{ c.personName }} · {{ relationLabel(c.relationType) }}</span><span class="small muted">合同 {{ c.contractId }}</span>
          </div>
        </template>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>人员钥匙包</h2><span class="small muted">{{ selected?.personName || '未选择' }}</span></div>
        <div v-if="!selected" class="empty">请选择人员</div>
        <div v-else-if="!grants.length" class="empty">暂无有效授权</div>
        <div v-for="g in grants" :key="g.id" class="row" style="padding:9px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1">
            <div>{{ g.targetName || g.targetType }}</div>
            <div class="small muted">{{ g.targetType }} · {{ g.validStart }} ~ {{ g.validEnd || '长期' }}</div>
          </div>
          <span class="badge blue">{{ g.grantLevel }}</span>
        </div>
      </div>
    </div>

    <div v-if="editingPerson" class="modal-mask" @click.self="editingPerson = null">
      <div class="modal">
        <div class="panel-head"><h2>编辑人员</h2><button class="sm" @click="editingPerson = null">关闭</button></div>
        <div class="field"><label>人员编码</label><input v-model="personEditForm.personCode" disabled /></div>
        <div class="field"><label>姓名</label><input v-model="personEditForm.personName" /></div>
        <div class="field"><label>手机号</label><input v-model="personEditForm.phone" /></div>
        <div class="field"><label>人员类型</label><select v-model="personEditForm.personType"><option value="GUARANTEE_TENANT">保障对象</option><option value="APPLICANT">申请人</option><option value="COHABITANT">同住人</option><option value="STAFF">工作人员</option></select></div>
        <div class="field"><label>性别</label><select v-model="personEditForm.gender"><option value="">未知</option><option value="MALE">男</option><option value="FEMALE">女</option></select></div>
        <div class="field"><label>地址</label><input v-model="personEditForm.address" /></div>
        <div class="field"><label>工作单位</label><input v-model="personEditForm.employer" /></div>
        <div class="field"><label>备注</label><input v-model="personEditForm.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="savePersonEdit">保存</button></div>
      </div>
    </div>

    <div v-if="selected" class="panel">
      <div class="panel-head"><div><h2>人员关系</h2><p>{{ selected.personName }} · 项目/房屋/空间关系</p></div><span class="small muted">{{ relations.length }} 条</span></div>
      <div class="row">
        <div class="field"><label>类型</label><select v-model="relForm.targetType" @change="relForm.targetId = ''"><option value="HOUSE">房屋</option><option value="PROJECT">项目</option></select></div>
        <div class="field" style="flex:2"><label>关联对象</label>
          <SearchSelect v-if="relForm.targetType === 'HOUSE'" v-model="relForm.targetId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" placeholder="搜索房屋" />
          <SearchSelect v-else v-model="relForm.targetId" :options="projects" label-key="orgName" sublabel-key="orgCode" value-key="id" placeholder="搜索项目" />
        </div>
        <div class="field"><label>关系</label><select v-model="relForm.relationType"><option value="TENANT">承租人</option><option value="FAMILY">家庭成员</option><option value="COHABITANT">同住人</option><option value="OWNER">产权人</option></select></div>
        <div class="field"><label>开始</label><input v-model="relForm.startDate" type="date" /></div>
        <div class="field"><label>结束</label><input v-model="relForm.endDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addRelation">新增关系</button></div>
      </div>
      <div v-if="!relations.length" class="empty">暂无关系</div>
      <div v-for="r in relations" :key="r.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
        <div style="flex:1"><div>{{ r.targetName }} · {{ relationLabel(r.relationType) }}</div><div class="small muted">{{ r.startDate || '' }} ~ {{ r.endDate || '长期' }}</div></div>
        <span class="badge green">{{ relationStatusLabel(r.status) }}</span>
        <button class="sm danger" :disabled="busy" @click="removeRelation(r)">移除</button>
      </div>
    </div>
  </div>
</template>
