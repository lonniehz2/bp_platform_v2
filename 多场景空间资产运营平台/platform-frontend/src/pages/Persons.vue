<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const persons = ref([])
const grants = ref([])
const relations = ref([])
const projects = ref([])
const houses = ref([])
const project = ref(null)
const selected = ref(null)
const error = ref('')
const busy = ref(false)
const page = ref(1)
const relForm = reactive({ targetType: 'HOUSE', targetId: '', relationType: 'TENANT', startDate: '', endDate: '' })
const form = reactive({ personCode: '', personName: '', phone: '', idCardMask: '', personType: 'GUARANTEE_TENANT', gender: '', birthDate: '', address: '', employer: '', emergencyContact: '', remark: '' })
const paged = computed(() => persons.value.slice((page.value - 1) * 10, page.value * 10))

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
  try { grants.value = await api.keyring(p.id); relations.value = await api.relations(p.id) } catch { grants.value = []; relations.value = [] }
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

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>人员档案</h2><p>保障对象、家庭成员、承租人、同住人、访客、服务人员</p></div><span class="badge blue">{{ persons.length }} 人</span></div>
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
        <div v-if="!persons.length" class="empty">暂无人员</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>人员编码</th><th>姓名</th><th>手机号</th><th>性别</th><th>类型</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="p in paged" :key="p.id" @click="selectPerson(p)" style="cursor:pointer">
                <td class="mono">{{ p.personCode }}</td><td>{{ p.personName }}</td><td>{{ p.phone || '-' }}</td>
                <td>{{ p.gender === 'MALE' ? '男' : p.gender === 'FEMALE' ? '女' : '-' }}</td>
                <td>{{ p.personType || '-' }}</td><td><span class="badge green">{{ p.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
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

    <div v-if="selected" class="panel">
      <div class="panel-head"><div><h2>人员关系</h2><p>{{ selected.personName }} · 项目/房屋/空间关系</p></div><span class="small muted">{{ relations.length }} 条</span></div>
      <div class="row">
        <div class="field"><label>类型</label><select v-model="relForm.targetType" @change="relForm.targetId = ''"><option value="HOUSE">房屋</option><option value="PROJECT">项目</option></select></div>
        <div class="field" style="flex:2"><label>关联对象</label>
          <select v-model="relForm.targetId">
            <template v-if="relForm.targetType === 'HOUSE'"><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></template>
            <template v-else><option v-for="p in projects" :key="p.id" :value="p.id">{{ p.orgName }}（{{ p.orgCode }}）</option></template>
          </select>
        </div>
        <div class="field"><label>关系</label><select v-model="relForm.relationType"><option value="TENANT">承租人</option><option value="FAMILY">家庭成员</option><option value="COHABITANT">同住人</option><option value="OWNER">产权人</option></select></div>
        <div class="field"><label>开始</label><input v-model="relForm.startDate" type="date" /></div>
        <div class="field"><label>结束</label><input v-model="relForm.endDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addRelation">新增关系</button></div>
      </div>
      <div v-if="!relations.length" class="empty">暂无关系</div>
      <div v-for="r in relations" :key="r.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
        <div style="flex:1"><div>{{ r.targetName }} · {{ r.relationType }}</div><div class="small muted">{{ r.startDate || '' }} ~ {{ r.endDate || '长期' }}</div></div>
        <span class="badge green">{{ r.status }}</span>
      </div>
    </div>
  </div>
</template>
