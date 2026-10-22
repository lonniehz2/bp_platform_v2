<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">日房态</h3>
      <el-tag size="small" type="info"></el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字/ID" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-input v-model="houseId" placeholder="房源ID"
                style="width:210px" />
      <el-button type="primary" @click="reload">按房源查</el-button>
      <el-button type="success" @click="openBook" data-testid="cal-book">预订</el-button>
      <el-button type="warning" plain @click="openRelease" data-testid="cal-release">释放</el-button>
      <el-radio-group v-model="viewMode" size="small" data-testid="cal-view-mode">
        <el-radio-button value="grid">月历</el-radio-button>
        <el-radio-button value="table">明细</el-radio-button>
      </el-radio-group>
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="'日房态用于短租与预订占用；改价只影响指定日期；点月历格子可直接操作'"
              style="margin-bottom:12px" />

    <!-- 月历宫格：酒店/民宿前台视角 -->
    <div v-if="viewMode === 'grid'" class="cal-grid" v-loading="loading">
      <div class="cal-head">
        <span v-for="w in WEEK" :key="w">{{ w }}</span>
      </div>
      <div class="cal-body">
        <div v-for="(d, i) in gridCells" :key="i" class="cal-cell"
             :class="[d.dayStatus ? 'st-' + d.dayStatus.toLowerCase() : 'st-empty', { pad: !d.date }]">
          <template v-if="d.date">
            <div class="cal-day">{{ Number(String(d.date).slice(8, 10)) }}</div>
            <div class="cal-tag">{{ d.dayStatusLabel || enumLabel('dayStatus', d.dayStatus) }}</div>
            <div v-if="d.price" class="cal-price">¥{{ d.price }}</div>
            <el-dropdown trigger="click" @command="(c) => onDayCommand(c, d)">
              <span class="cal-more">⋯</span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="book">预订这一天</el-dropdown-item>
                  <el-dropdown-item command="close">标记停用</el-dropdown-item>
                  <el-dropdown-item command="open">恢复可售</el-dropdown-item>
                  <el-dropdown-item command="price" divided>设置价格</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </div>
    </div>

    <el-table v-else :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="houseId" label="房源" width="120">
        <template #default="{ row }">{{ houseLabel || row.houseIdName || row.houseId }}</template>
      </el-table-column>
      <el-table-column prop="date" label="日期" width="120" />
      <el-table-column prop="dayStatus" label="日状态" width="110">
        <template #default="{ row }">{{ row.dayStatusLabel || enumLabel('dayStatus', row.dayStatus) }}</template>
      </el-table-column>
      <el-table-column prop="bookingId" label="占用订单" width="150">
        <template #default="{ row }">{{ row.orderIdName || row.orderId }}</template>
      </el-table-column>
      <el-table-column label="操作" :width="ROWACTIONS ? 210 : 110" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" @click="bookForHouse(row)">预订</el-button>
          <el-button link @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="viewMode === 'table'" style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <!-- 写操作表单（字段按后端 Cmd 定义配置） -->
    <el-dialog v-model="formVisible" :title="formTitle" width="560px">
      <el-form :model="model" label-width="120px">
        <el-form-item v-for="f in fields" :key="f.key" :label="f.label">
          <el-input v-if="f.type === 'text'" v-model="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'textarea'" type="textarea" :rows="3"
                    v-model="model[f.key]" :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'number'" v-model.number="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-date-picker v-else-if="f.type === 'date'" v-model="model[f.key]"
                          type="date" value-format="YYYY-MM-DD" style="width:100%" />
          <el-select v-else-if="f.type === 'select'" v-model="model[f.key]"
                     style="width:100%">
            <el-option v-for="o in f.options" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>
          <el-switch v-else-if="f.type === 'bool'" v-model="model[f.key]" />
        </el-form-item>
      </el-form>
      <el-alert v-if="formNote" :closable="false" show-icon type="warning"
                :title="formNote" style="margin-top:8px" />
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 预订 -->
    <el-dialog v-model="bookVisible" title="预订房源（按日）" width="560px">
      <el-form :model="bf" label-width="100px">
        <el-form-item label="房源 ID" required>
          <el-input v-model="bf.houseId" placeholder="可从列表行点「预订」自动带入" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="入住日" required>
            <el-date-picker v-model="bf.checkIn" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="退房日" required>
            <el-date-picker v-model="bf.checkOut" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="占用类型">
            <el-select v-model="bf.targetStatus" style="width:100%">
              <el-option label="预订（BOOKED）" value="BOOKED" />
              <el-option label="直接入住（OCCUPIED）" value="OCCUPIED" />
            </el-select></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="bf.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <el-alert type="info" :closable="false"
                title="区间左闭右开：11-01 入住、11-03 退房，占用 11-01 与 11-02 两晚" />
      <template #footer>
        <el-button @click="bookVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doBook">确认预订</el-button>
      </template>
    </el-dialog>

    <!-- 释放 -->
    <el-dialog v-model="releaseVisible" title="释放房态" width="520px">
      <el-form :model="rf" label-width="100px">
        <el-form-item label="房源 ID" required><el-input v-model="rf.houseId" /></el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="起始日" required>
            <el-date-picker v-model="rf.checkIn" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="结束日" required>
            <el-date-picker v-model="rf.checkOut" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="releaseVisible = false">取消</el-button>
        <el-button type="warning" :loading="saving" @click="doRelease">释放</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { calendarApi } from '@/api/modules'
import req from '@/api/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const month = ref(new Date().toISOString().slice(0, 7))
const detailVisible = ref(false)
const detail = ref(null)

const formVisible = ref(false)
const formTitle = ref('')
const formNote = ref('')
const fields = []
const model = reactive({})

// 必填字段（取自后端 Cmd 的 @NotNull）
const REQUIRED = []
let submitFn = null
const houseId = ref(null)
const houseLabel = ref('')

/**
 * 进入页面时自动定位房源并加载当月日历：
 * 优先用路由 query 的 houseId，其次取第一个酒店/民宿房源（日房态主要服务短租场景）。
 */
async function autoLoadMonth() {
  if (!houseId.value) {
    const q = new URLSearchParams(window.location.hash.split('?')[1] || '')
    if (q.get('houseId')) {
      houseId.value = q.get('houseId')
    }
  }
  if (!houseId.value) {
    try {
      const d = await req.get('/houses', { params: { pageNum: 1, pageSize: 1, houseType: 'HOTEL' } })
      const list = (d && d.rows) || []
      if (list.length) {
        houseId.value = String(list[0].id)
        houseLabel.value = list[0].houseName || String(list[0].id)
      }
    } catch (e) { /* 忽略 */ }
  }
  if (houseId.value) {
    await load()
  }
}
onMounted(autoLoadMonth)

async function load() {
  if (!houseId.value) {
    ElMessage.warning("请先输入房源ID")
    return
  }
  loading.value = true
  try {
    // 月格子可能尚未生成：先 ensure（幂等），再取月历
    await calendarApi.ensure(houseId.value, month.value)
    const data = await calendarApi.byHouse(houseId.value, { month: month.value })
    const cells = Array.isArray(data) ? data : (data.rows || [])
    rows.value = cells.filter((c) => {
      if (!keyword.value) return true
      return String(c.date || '').includes(keyword.value)
    })
    total.value = rows.value.length
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}

function reload() { pageNum.value = 1; load() }
function openDetail(row) { detail.value = row; detailVisible.value = true }

function openForm(title, fieldDefs, fn, preset = {}, note = '') {
  formTitle.value = title
  formNote.value = note
  Object.keys(model).forEach((k) => delete model[k])
  fieldDefs.forEach((f) => { model[f.key] = preset[f.key] ?? f.default ?? '' })
  submitFn = fn
  formVisible.value = true
}

/** 必填校验（字段级，依赖后端 Cmd 的 @NotNull 语义）。 */
function validateForm() {
  const missing = fields.filter((f) => REQUIRED.includes(f.key)
    && (model[f.key] === '' || model[f.key] === null || model[f.key] === undefined))
  if (missing.length) {
    ElMessage.warning('请填写：' + missing.map((f) => f.label).join('、'))
    return false
  }
  // 数字类基本合法性
  for (const f of fields) {
    if (f.type === 'number' && model[f.key] !== '' && model[f.key] !== null
        && Number.isNaN(Number(model[f.key]))) {
      ElMessage.warning(f.label + '必须是数字')
      return false
    }
  }
  return true
}

async function submit() {
  if (!validateForm()) return
  saving.value = true
  try {
    await submitFn({ ...model })
    ElMessage.success('操作成功')
    formVisible.value = false
    load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}


function resetQuery() {
  houseId.value = ''
  keyword.value = ''
  pageNum.value = 1
  reload()
}


/** 日房态：预订 / 释放（酒店民宿场景） */
const bookVisible = ref(false)
const releaseVisible = ref(false)
const bf = reactive({ houseId: '', checkIn: '', checkOut: '', targetStatus: 'BOOKED', remark: '' })
const rf = reactive({ houseId: '', checkIn: '', checkOut: '' })

function openBook() {
  Object.assign(bf, { houseId: '', checkIn: '', checkOut: '', targetStatus: 'BOOKED', remark: '' })
  bookVisible.value = true
}

function bookForHouse(row) {
  openBook()
  bf.houseId = String(row.houseId || '')
  bf.checkIn = row.calendarDate || ''
}

function openRelease() {
  Object.assign(rf, { houseId: '', checkIn: '', checkOut: '' })
  releaseVisible.value = true
}

async function doBook() {
  if (!bf.houseId || !bf.checkIn || !bf.checkOut) {
    ElMessage.warning('请填写房源与起止日期'); return
  }
  saving.value = true
  try {
    const n = await req.post('/house-calendar/book', {
      houseId: bf.houseId, checkIn: bf.checkIn, checkOut: bf.checkOut,
      sourceType: 'MANUAL', targetStatus: bf.targetStatus, remark: bf.remark
    })
    ElMessage.success(`已锁定 ${n} 天`)
    bookVisible.value = false
    reload()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '预订失败（可能该区间已被占用）')
  } finally { saving.value = false }
}

/** 释放某区间（把占用/停用恢复为可售） */
async function doRelease() {
  if (!rf.houseId || !rf.checkIn || !rf.checkOut) {
    ElMessage.warning('请填写房源与起止日期'); return
  }
  saving.value = true
  try {
    const n = await req.post('/house-calendar/release', {
      houseId: rf.houseId, checkIn: rf.checkIn, checkOut: rf.checkOut
    })
    ElMessage.success(`已释放 ${n} 天`)
    releaseVisible.value = false
    reload()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '释放失败')
  } finally { saving.value = false }
}

/** 视图模式：月历（酒店前台视角）/ 明细（逐日表格） */
const viewMode = ref('grid')
const WEEK = ['一', '二', '三', '四', '五', '六', '日']

/** 月历格子：按当月 1 日星期补空格，保持 7 列对齐 */
const gridCells = computed(() => {
  const cells = rows.value || []
  if (!cells.length) return []
  const first = String(cells[0].date || '')
  const d = new Date(first + 'T00:00:00')
  const lead = (d.getDay() + 6) % 7   // 周一为一周开始
  const pad = Array.from({ length: lead }, () => ({ date: null }))
  return [...pad, ...cells]
})

/** 格子操作：预订 / 停用 / 恢复 / 改价 */
async function onDayCommand(cmd, cell) {
  const date = String(cell.date)
  try {
    if (cmd === 'book') {
      openBook()
      bf.houseId = String(houseId.value)
      bf.checkIn = date
      bf.checkOut = nextDay(date)
      return
    }
    if (cmd === 'close' || cmd === 'open') {
      const dayStatus = cmd === 'close' ? 'CLOSED' : 'FREE'
      await req.post(`/house-calendar/${houseId.value}/status`, {
        start: date, end: nextDay(date), dayStatus,
        remark: cmd === 'close' ? '手工停用' : '恢复可售'
      })
      ElMessage.success(cmd === 'close' ? '已标记停用' : '已恢复可售')
      load()
      return
    }
    if (cmd === 'price') {
      const { value } = await ElMessageBox.prompt(`${date} 单价（元）`, '设置单日价格', {
        inputValue: String(cell.price || ''),
        inputPattern: /^\d+(\.\d{1,2})?$/,
        inputErrorMessage: '请输入数字，最多两位小数'
      })
      await req.post(`/house-calendar/${houseId.value}/price`, {
        start: date, end: nextDay(date), price: Number(value)
      })
      ElMessage.success('价格已更新')
      load()
    }
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

function nextDay(date) {
  const d = new Date(date + 'T00:00:00')
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}
</script>

<style scoped>
.cal-grid { border: 1px solid var(--el-border-color-light); border-radius: 6px; overflow: hidden; }
.cal-head { display: grid; grid-template-columns: repeat(7, 1fr); background: var(--el-fill-color-light); }
.cal-head span { padding: 8px; text-align: center; font-size: 13px; color: var(--el-text-color-secondary); }
.cal-body { display: grid; grid-template-columns: repeat(7, 1fr); }
.cal-cell { min-height: 92px; padding: 6px 8px; border-top: 1px solid var(--el-border-color-lighter);
            border-right: 1px solid var(--el-border-color-lighter); position: relative; }
.cal-cell.pad { background: var(--el-fill-color-lighter); }
.cal-day { font-size: 14px; font-weight: 600; }
.cal-tag { font-size: 12px; margin-top: 4px; }
.cal-price { font-size: 12px; color: var(--el-color-danger); margin-top: 2px; }
.cal-more { position: absolute; right: 6px; top: 4px; cursor: pointer; color: var(--el-text-color-placeholder); }
.st-free { background: #f6ffed; }
.st-booked { background: #fff7e6; }
.st-occupied { background: #fff1f0; }
.st-closed { background: #f5f5f5; color: var(--el-text-color-placeholder); }
</style>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
