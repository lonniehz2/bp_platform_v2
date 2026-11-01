<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">{{ t('message.title') }}</h3>
        <el-tag type="danger" size="small" v-if="unread > 0">未读 {{ unread }}</el-tag>
        <div class="spacer" />
        <el-select v-model="query.status" :placeholder="t('message.status')" clearable
                   style="width:130px" @change="load">
          <el-option :label="t('message.unread')" value="PENDING" />
          <el-option :label="t('message.read')" value="READ" />
          <el-option :label="t('message.done')" value="DONE" />
        </el-select>
        <el-switch v-model="onlyMine" active-text="只看我的" inline-prompt
                   data-testid="msg-only-mine" @change="load" />
        <el-button type="primary" @click="load">{{ t('message.refresh') }}</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="title" :label="t('message.titleCol')" min-width="220" />
        <el-table-column prop="content" :label="t('message.content')" min-width="260"
                         show-overflow-tooltip />
        <el-table-column prop="todoType" :label="t('message.type')" width="110">
          <template #default="{ row }">{{ row.todoTypeLabel || enumLabel('todoType', row.todoType) }}</template>
        </el-table-column>
        <el-table-column prop="priority" :label="t('message.priority')" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="priorityTone(row.priority)">
              {{ row.priorityLabel || enumLabel('priority', row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="todoStatus" :label="t('message.statusCol')" width="100">
          <template #default="{ row }">{{ row.todoStatusLabel || enumLabel('todoStatus', row.todoStatus) }}</template>
        </el-table-column>
        <el-table-column prop="createTime" :label="t('message.created')" width="170" />
        <el-table-column :label="t('message.actions')" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('message.detail') }}</el-button>
            <el-button link type="primary" :disabled="row.todoStatus !== 'PENDING'"
                       @click="markRead(row)">已读</el-button>
            <el-button link type="success" :disabled="row.todoStatus === 'DONE'"
                       @click="markDone(row)">办结</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                     :total="+total || 0" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">发送通知</h4>
      <el-form :model="form" label-width="100px" style="max-width:620px">
        <el-form-item :label="t('message.recipient')">
          <el-input v-model="form.userId" />
        </el-form-item>
        <el-form-item :label="t('message.titleCol')">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item :label="t('message.contentLabel')">
          <el-input v-model="form.content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="t('message.priority')">
          <el-radio-group v-model="form.priority">
            <el-radio value="URGENT">紧急</el-radio>
            <el-radio value="IMPORTANT">重要</el-radio>
            <el-radio value="NORMAL">普通</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="send">{{ t('message.create') }}</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('message.detail')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import DetailView from '@/components/DetailView.vue'
import { ElMessage } from 'element-plus'
import { msgApi } from '@/api/modules'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const unread = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, status: '' })
/**
 * 只看我的：默认关闭。
 * 待办中心的分类数字是全租户口径，若这里默认只查本人，两边数量就对不上
 * （此前「待办消息 9 条」点进来只有 3 条，就是这个原因）。
 */
const onlyMine = ref(false)
// 从待办中心「待办消息」跳转过来时带 pending=1：按待处理筛选并看全部
if (/pending=1/.test(window.location.hash)) {
  query.status = 'PENDING'
  onlyMine.value = false
}
const form = reactive({ userId: null, title: '', content: '', priority: 'NORMAL' })

function priorityTone(p) {
  return ({ URGENT: 'danger', IMPORTANT: 'warning' })[p] || 'info'
}

async function load() {
  loading.value = true
  try {
    const data = await msgApi.todos({
      pageNum: query.pageNum, pageSize: query.pageSize,
      userId: onlyMine.value ? (auth.user?.userId || undefined) : undefined,
      status: query.status || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
    if (auth.user?.userId) {
      unread.value = Number(await msgApi.unread(auth.user.userId) || 0)
    }
  } finally {
    loading.value = false
  }
}

async function markRead(row) {
  await msgApi.read(row.id)
  ElMessage.success('已标记已读')
  load()
}

async function markDone(row) {
  await msgApi.done(row.id)
  ElMessage.success('已办结')
  load()
}

async function send() {
  if (!form.userId || !form.title) {
    ElMessage.warning('接收人与标题必填')
    return
  }
  saving.value = true
  try {
    await msgApi.createTodo({ ...form, todoType: 'REMIND' })
    ElMessage.success('待办已创建')
    form.title = ''
    form.content = ''
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
