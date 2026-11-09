<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'
import Pager from '../components/Pager.vue'
import { confirmAction } from '../confirm'

const project = ref(null)
const houses = ref([])
const meters = ref([])
const summary = ref([])
const readings = ref([])
const selected = ref(null)
const page = ref(1)
const error = ref('')
const busy = ref(false)
const form = reactive({ houseId: '', meterType: 'WATER', meterNo: '', initialReading: 0 })
const readForm = reactive({ meterId: '', readingDate: '', readingValue: '', readerName: '抄表员' })
const editing = ref(null)
const editForm = reactive({ houseId: '', meterType: 'WATER', meterNo: '', installDate: '' })
const paged = computed(() => meters.value.slice((page.value - 1) * 10, page.value * 10))
const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

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
    const id = project.value.id
    const [h, m, s] = await Promise.all([api.houses(id), api.meters(id), api.meterSummary(id)])
    houses.value = h; meters.value = m; summary.value = s
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!selected.value && m.length) selectMeter(m[0])
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.meterNo.trim()) throw new Error('请填写表号')
    await api.createMeter({
      projectId: project.value.id, houseId: form.houseId,
      meterType: form.meterType, meterNo: form.meterNo.trim(),
      initialReading: Number(form.initialReading || 0)
    })
    form.meterNo = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function selectMeter(m) {
  selected.value = m
  readings.value = await api.meterReadings(m.id)
}

async function read() {
  busy.value = true; error.value = ''
  try {
    if (!readForm.readingValue) throw new Error('请填写本次读数')
    await api.readMeter(selected.value.id, {
      readingDate: readForm.readingDate || null,
      readingValue: Number(readForm.readingValue),
      readerName: readForm.readerName
    })
    readForm.readingValue = ''
    await load()
    await selectMeter(meters.value.find(m => String(m.id) === String(selected.value.id)) || selected.value)
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


function openEdit(m) {
  editing.value = m
  Object.assign(editForm, { houseId: m.houseId || '', meterType: m.meterType || 'WATER', meterNo: m.meterNo || '', installDate: m.installDate || '' })
}

async function saveEdit() {
  busy.value = true; error.value = ''
  try {
    await api.updateMeter(editing.value.id, { ...editForm })
    editing.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function toggleStatus(m) {
  const next = m.meterStatus === 'ACTIVE' ? 'DISABLED' : 'ACTIVE'
  if (!await confirmAction({ title: '变更表计状态', message: `确认将表计 ${m.meterNo} 设为 ${next}？`, confirmText: '确认' })) return
  busy.value = true; error.value = ''
  try { await api.updateMeterStatus(m.id, next); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid cards">
      <div class="card"><div class="label">表计数量</div><div class="value">{{ meters.length }}</div><div class="hint">水/电/气</div></div>
      <div v-for="s in summary" :key="s.meterType" class="card">
        <div class="label">{{ s.meterType }}</div><div class="value">{{ s.meterCount }}</div><div class="hint">用量 {{ money(s.usageAmount) }}</div>
      </div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><div><h2>表计台账</h2><p>{{ project?.orgName || '未选择项目' }} · 水表/电表/燃气表</p></div></div>
      <div class="row">
        <div class="field"><label>房屋</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" placeholder="搜索房屋" /></div>
        <div class="field"><label>类型</label><select v-model="form.meterType"><option value="WATER">水表</option><option value="ELECTRICITY">电表</option><option value="GAS">燃气表</option></select></div>
        <div class="field"><label>表号</label><input v-model="form.meterNo" placeholder="如 WM-001" /></div>
        <div class="field"><label>初始读数</label><input v-model.number="form.initialReading" type="number" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">新增表计</button></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns: 1.2fr .8fr">
      <div class="panel">
        <div class="panel-head"><h2>表计列表</h2><span class="small muted">点击查看抄表记录</span></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>表号</th><th>类型</th><th>房屋</th><th>上次读数</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="m in paged" :key="m.id" @click="selectMeter(m)" style="cursor:pointer">
                <td class="mono">{{ m.meterNo }}</td><td>{{ m.meterType }}</td><td>{{ m.houseName }}</td>
                <td>{{ money(m.currentReading) }}</td><td><span class="badge" :class="m.meterStatus === 'ACTIVE' ? 'green' : 'orange'">{{ m.meterStatus }}</span></td>
                <td><button v-if="can('asset')" class="sm" @click.stop="openEdit(m)">编辑</button> <button v-if="can('asset')" class="sm" :class="m.meterStatus === 'ACTIVE' ? 'danger' : ''" @click.stop="toggleStatus(m)">{{ m.meterStatus === 'ACTIVE' ? '停用' : '启用' }}</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pager :total="meters.length" :page="page" @update:page="page = $event" />
      </div>

      <div class="panel">
        <div class="panel-head"><h2>抄表</h2><span class="small muted">{{ selected?.meterNo || '未选择' }}</span></div>
        <div v-if="!selected" class="empty">请选择表计</div>
        <template v-else>
          <div class="row" style="margin-bottom:10px">
            <div class="field"><label>本次读数</label><input v-model.number="readForm.readingValue" type="number" /></div>
            <div class="field"><label>日期</label><input v-model="readForm.readingDate" type="date" /></div>
            <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="read">保存抄表</button></div>
          </div>
          <div v-if="!readings.length" class="empty">暂无抄表记录</div>
          <div v-for="r in readings" :key="r.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
            <div style="flex:1"><div>{{ r.readingDate }}</div><div class="small muted">{{ r.previousValue }} → {{ r.readingValue }}</div></div>
            <span class="badge blue">用量 {{ money(r.usageAmount) }}</span>
          </div>
        </template>
      </div>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <div class="panel-head"><h2>编辑表计</h2><button class="sm" @click="editing = null">关闭</button></div>
        <div class="field"><label>表号</label><input v-model="editForm.meterNo" /></div>
        <div class="field"><label>类型</label><select v-model="editForm.meterType"><option value="WATER">水表</option><option value="ELECTRICITY">电表</option><option value="GAS">燃气表</option></select></div>
        <div class="field"><label>房屋</label><SearchSelect v-model="editForm.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" placeholder="搜索房屋" /></div>
        <div class="field"><label>安装日期</label><input v-model="editForm.installDate" type="date" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveEdit">保存</button></div>
      </div>
    </div>
  </div>
</template>
