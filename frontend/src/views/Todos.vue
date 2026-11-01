<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('todo.title') }}</h3>
      <el-tag v-if="total > 0" type="danger" effect="dark" data-testid="todo-total">
        {{ t('todo.totalTag', { n: total }) }}
      </el-tag>
      <el-tag v-else type="success" effect="plain">{{ t('todo.none') }}</el-tag>
      <div class="spacer" />
      <el-checkbox v-model="onlyMine" @change="search" data-testid="todo-only-mine">
        {{ t('todo.onlyMine') }}
      </el-checkbox>
      <el-button type="success" :disabled="!selection.length" @click="batchDone">{{ t('todo.batchDone') }}
        批量完成{{ selection.length ? '（' + selection.length + '）' : '' }}
      </el-button>
      <el-button :disabled="!selection.length" @click="batchRead">{{ t('todo.batchRead') }}
        批量已读{{ selection.length ? '（' + selection.length + '）' : '' }}
      </el-button>
      <el-button @click="loadAll">{{ t('todo.refresh') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
              title="{{ t('todo.tip') }}" />

    <!-- 四个总览指标 -->
    <el-row :gutter="12" style="margin-bottom:6px">
      <el-col :span="6" v-for="c in summary" :key="c.key">
        <div class="ov-card" :class="c.tone" @click="c.route && go(c.route)">
          <div class="ov-num">{{ c.count }}</div>
          <div class="ov-label">{{ c.label }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 各模块待办 -->
    <div class="sec-title">{{ t('todo.modSections') }}</div>
    <el-row :gutter="12">
      <el-col :span="6" v-for="c in categories" :key="c.key" style="margin-bottom:12px">
        <div class="cat-card" :class="{ zero: c.count === 0 }" @click="go(c.route)">
          <div class="cat-head">
            <span class="cat-label">{{ c.label }}</span>
            <span class="cat-count">{{ c.count }}</span>
          </div>
          <div class="cat-hint">{{ c.hint }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 待办明细 -->
    <div class="sec-title">{{ t('todo.detail') }}</div>
    <div class="filter-bar">
      <el-input v-model="query.keyword" :placeholder="t('todo.keyword')" clearable
                style="width:200px" data-testid="todo-keyword"
                @keyup.enter="search" />
      <el-select v-model="query.todoType" :placeholder="t('todo.type')" clearable style="width:130px">
        <el-option :label="t('todo.approval')" value="APPROVAL" />
        <el-option :label="t('todo.remind')" value="REMIND" />
        <el-option :label="t('todo.task')" value="TASK" />
        <el-option :label="t('todo.handle')" value="HANDLE" />
      </el-select>
      <el-date-picker v-model="query.dateRange" type="daterange" unlink-panels
                      value-format="YYYY-MM-DD" range-separator="~"
                      :shortcuts="dateShortcuts"
                      :start-placeholder="t('todo.start')" :end-placeholder="t('todo.end')"
                      style="width:250px" data-testid="todo-range" />
      <el-select v-model="query.status" :placeholder="t('todo.status')" clearable style="width:120px">
        <el-option :label="t('todo.pending')" value="PENDING" />
        <el-option :label="t('todo.done')" value="DONE" />
      </el-select>
      <el-button type="primary" @click="search" data-testid="todo-search">{{ t('todo.search') }}</el-button>
      <el-button @click="resetQuery" data-testid="todo-reset">{{ t('todo.reset') }}</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small"
              @selection-change="(v) => (selection = v)">
      <el-table-column type="selection" width="42"
                       :selectable="(row) => row.todoStatus !== 'DONE'" />
      <el-table-column prop="title" :label="t('todo.titleCol')" min-width="220" />
      <el-table-column :label="t('todo.typeCol')" width="100">
        <template #default="{ row }">{{ enumLabel('todoType', row.todoType) || row.todoTypeLabel }}</template>
      </el-table-column>
      <el-table-column :label="t('todo.statusCol')" width="95">
        <template #default="{ row }">
          <el-tag size="small" :type="row.todoStatus === 'DONE' ? 'success' : 'warning'">
            {{ row.todoStatusLabel || enumLabel('todoStatus', row.todoStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="bizType" :label="t('todo.biz')" width="120" />
      <el-table-column prop="createTime" :label="t('todo.created')" width="165" />
      <el-table-column :label="t('todo.actions')" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goDeal(row)" data-testid="todo-deal">{{ t('todo.deal') }}</el-button>
          <el-button link type="primary" :disabled="row.todoStatus === 'DONE'"
                     @click="finish(row)">标记完成</el-button>
          <el-button link :disabled="row.todoStatus === 'DONE'"
                     @click="readOne(row)">标记已读</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+totalRows || 0" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; loadTodos() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; loadTodos() }" />
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { enumLabel } from '@/constants/enums'
import { msgApi } from '@/api/modules'
import { useTodoStore } from '@/store/todo'
import { useAuthStore } from '@/store/auth'

const { t } = useI18n()
const router = useRouter()
const todoStore = useTodoStore()
const auth = useAuthStore()
const loading = ref(false)
const categories = ref([])
const rows = ref([])
const totalRows = ref(0)
const selection = ref([])

const total = computed(() =>
  categories.value.reduce((s, c) => s + Number(c.count || 0), 0))

/** 顶部四个指标：总量 / 消息 / 业务待办 / 工单 */
const summary = computed(() => {
  const find = (k) => categories.value.find((c) => c.key === k)
  const todo = find('TODO')
  const workorder = find('WORKORDER')
  const biz = categories.value
    .filter((c) => c.key !== 'TODO' && c.key !== 'WORKORDER')
    .reduce((s, c) => s + Number(c.count || 0), 0)
  return [
    { key: 'ALL', label: t('todo.summaryAll'), count: total.value, tone: 'tone-all', route: null },
    { key: 'TODO', label: t('todo.summaryTodo'), count: todo ? todo.count : 0, tone: 'tone-todo', route: todo?.route },
    { key: 'BIZ', label: t('todo.summaryBiz'), count: biz, tone: 'tone-biz', route: null },
    { key: 'WO', label: t('todo.summaryWo'), count: workorder ? workorder.count : 0, tone: 'tone-wo', route: workorder?.route }
  ]
})

/** 筛选条件：默认只看「待处理」 */
const DEFAULT_QUERY = () => ({
  pageNum: 1,
  pageSize: 20,
  keyword: '',
  todoType: '',
  status: 'PENDING',
  dateRange: []
})
const query = reactive(DEFAULT_QUERY())
/** 只看指派给我的待办（按登录用户过滤） */
const onlyMine = ref(false)

/** 日期快捷选项：省掉手点日历 */
const dateShortcuts = [
  {
    text: t('todo.today'),
    value: () => {
      const d = new Date()
      return [d, d]
    }
  },
  {
    text: t('todo.last7'),
    value: () => {
      const e = new Date()
      const s = new Date()
      s.setDate(s.getDate() - 6)
      return [s, e]
    }
  },
  {
    text: t('todo.last30'),
    value: () => {
      const e = new Date()
      const s = new Date()
      s.setDate(s.getDate() - 29)
      return [s, e]
    }
  }
]

/** 关联业务 → 页面路由（待办未带 linkUrl 时兜底） */
const BIZ_ROUTE = {
  APPLICATION: '/applications',
  CONTRACT: '/contracts',
  TERMINATION: '/terminations',
  EXCHANGE: '/exchanges',
  BILL: '/bills',
  PAYMENT: '/bills',
  DEPOSIT: '/deposits',
  REVIEW: '/annual-reviews',
  WORKORDER: '/ops-center',
  COMPLAINT: '/complaints',
  ALERT: '/alerts',
  VISIT: '/visits',
  PERSON: '/persons',
  HOUSE: '/houses'
}

async function loadOverview() {
  try {
    const d = await msgApi.todoOverview()
    categories.value = d.categories || []
  } catch (e) {
    categories.value = []
  }
}

async function loadTodos() {
  loading.value = true
  try {
    const [startDate, endDate] = query.dateRange || []
    // 注意：后端参数名是 status，不是 todoStatus（传错会被静默忽略）
    const d = await msgApi.todos({
      pageNum: query.pageNum,
      pageSize: query.pageSize,
      status: query.status || undefined,
      todoType: query.todoType || undefined,
      keyword: query.keyword || undefined,
      userId: onlyMine.value ? auth.user?.userId : undefined,
      startDate: startDate || undefined,
      endDate: endDate || undefined
    })
    rows.value = d.rows || []
    totalRows.value = Number(d.total || 0)
  } catch (e) {
    rows.value = []
    totalRows.value = 0
  } finally {
    loading.value = false
  }
}

async function loadAll() {
  await Promise.all([loadOverview(), loadTodos()])
}

function search() {
  query.pageNum = 1
  loadTodos()
}

function resetQuery() {
  Object.assign(query, DEFAULT_QUERY())
  onlyMine.value = false
  loadTodos()
}

function go(route) {
  if (route) router.push(route)
}

/** 完成/已读之后同步刷新角标，避免侧边栏数字滞后 */
async function afterWrite() {
  await Promise.all([loadOverview(), todoStore.refresh()])
}

async function finish(row) {
  await msgApi.done(row.id)
  ElMessage.success('已标记完成')
  await afterWrite()
  loadTodos()
}

async function readOne(row) {
  await msgApi.read(row.id)
  ElMessage.success('已标记已读')
  loadTodos()
}

async function batchDone() {
  const targets = selection.value.filter((r) => r.todoStatus !== 'DONE')
  if (!targets.length) return
  let okCount = 0
  for (const r of targets) {
    try {
      await msgApi.done(r.id)
      okCount++
    } catch (e) {
      /* 单条失败不打断批量 */
    }
  }
  ElMessage.success(`已完成 ${okCount} / ${targets.length} 条`)
  await afterWrite()
  loadTodos()
}

async function batchRead() {
  const targets = selection.value.filter((r) => r.todoStatus !== 'DONE')
  if (!targets.length) return
  let okCount = 0
  for (const r of targets) {
    try {
      await msgApi.read(r.id)
      okCount++
    } catch (e) {
      /* 单条失败不打断批量 */
    }
  }
  ElMessage.success(`已读 ${okCount} / ${targets.length} 条`)
  loadTodos()
}

/**
 * 去处理：优先用待办自带的 linkUrl，没有就按 bizType 映射到对应列表页。
 * 不带业务参数跳转——筛选条件各页不同，硬塞可能筛出空列表，不如让用户自己定位。
 */
function goDeal(row) {
  if (row.linkUrl) {
    if (/^https?:/.test(row.linkUrl)) window.open(row.linkUrl, '_blank')
    else router.push(row.linkUrl)
    return
  }
  const route = BIZ_ROUTE[row.bizType]
  if (route) router.push(route)
  else ElMessage.warning('该待办没有关联页面')
}

onMounted(loadAll)
</script>

<style scoped>
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.ov-card {
  border: 1px solid #e8e8e8;
  border-radius: 2px;
  background: var(--bp-card-bg, #fff);
  padding: 14px 16px;
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.ov-card:hover { box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); }
.ov-num { font-size: 26px; font-weight: 600; line-height: 1.1; }
.ov-label { font-size: 13px; color: #8c8c8c; margin-top: 4px; }
.tone-all .ov-num { color: #1890ff; }
.tone-todo .ov-num { color: #faad14; }
.tone-biz .ov-num { color: #52c41a; }
.tone-wo .ov-num { color: #f5222d; }

.sec-title {
  font-size: 14px;
  font-weight: 600;
  color: #262626;
  margin: 16px 0 10px;
  padding-left: 8px;
  border-left: 3px solid #1890ff;
}

.cat-card {
  border: 1px solid #e8e8e8;
  border-radius: 2px;
  background: var(--bp-card-bg, #fff);
  padding: 12px 14px;
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.cat-card:hover { box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); }
.cat-card.zero { opacity: 0.55; }
.cat-head { display: flex; align-items: baseline; justify-content: space-between; }
.cat-label { font-size: 14px; color: #262626; }
.cat-count { font-size: 20px; font-weight: 600; color: #1890ff; }
.cat-card.zero .cat-count { color: #bfbfbf; }
.cat-hint { font-size: 12px; color: #8c8c8c; margin-top: 6px; }
</style>
