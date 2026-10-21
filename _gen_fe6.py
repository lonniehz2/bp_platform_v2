# -*- coding: utf-8 -*-
"""生成 PC 页面：组织管理 / 房源台账 / 消息待办中心 + 路由与菜单"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

F['src/views/Orgs.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">组织机构</h3>
        <div class="spacer" />
        <el-radio-group v-model="viewMode" size="small" @change="load">
          <el-radio-button value="tree">树形</el-radio-button>
          <el-radio-button value="table">列表</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="load">刷新</el-button>
      </div>

      <el-row :gutter="16">
        <el-col :span="7">
          <el-tree :data="tree" :props="{ label: 'orgName', children: 'children' }"
                   node-key="id" default-expand-all highlight-current
                   @node-click="onSelect" />
          <el-empty v-if="!tree.length" description="暂无组织" :image-size="60" />
        </el-col>
        <el-col :span="17">
          <el-table :data="rows" v-loading="loading" border size="small">
            <el-table-column prop="id" label="ID" width="150" />
            <el-table-column prop="orgName" label="组织名称" min-width="160" />
            <el-table-column prop="orgCode" label="编码" width="140" />
            <el-table-column prop="orgType" label="类型" width="110" />
            <el-table-column prop="parentId" label="上级" width="150" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                         :total="total" :page-size="query.pageSize"
                         :current-page="query.pageNum"
                         @current-change="(p) => { query.pageNum = p; load() }" />
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { orgApi } from '@/api/modules'

const loading = ref(false)
const tree = ref([])
const rows = ref([])
const total = ref(0)
const viewMode = ref('tree')
const query = reactive({ pageNum: 1, pageSize: 20, parentId: undefined })

async function loadTree() {
  try {
    const data = await orgApi.tree()
    tree.value = Array.isArray(data) ? data : (data?.rows || [])
  } catch (e) { tree.value = [] }
}

async function load() {
  loading.value = true
  try {
    const data = await orgApi.page({ ...query })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}

function onSelect(node) {
  query.parentId = node.id
  query.pageNum = 1
  load()
}

onMounted(async () => { await loadTree(); await load() })
</script>
'''

F['src/views/Houses.vue'] = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">房源台账</h3>
      <div class="spacer" />
      <el-select v-model="query.houseStatus" placeholder="房源状态" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
      </el-select>
      <el-select v-model="query.houseType" placeholder="房源类型" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="t in types" :key="t" :label="t" :value="t" />
      </el-select>
      <el-button type="primary" @click="reload">查询</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="houseCode" label="房源编号" width="150" />
      <el-table-column prop="houseName" label="名称" min-width="150" />
      <el-table-column prop="houseType" label="类型" width="110" />
      <el-table-column prop="area" label="面积(㎡)" width="100" />
      <el-table-column prop="rentStandard" label="租金标准" width="110" />
      <el-table-column prop="currentCapacity" label="现住/上限" width="110">
        <template #default="{ row }">
          {{ row.currentCapacity ?? 0 }} / {{ row.maxCapacity ?? 0 }}
        </template>
      </el-table-column>
      <el-table-column prop="houseStatusLabel" label="状态" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="statusTone(row.houseStatus)">
            {{ row.houseStatusLabel || row.houseStatus }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="vacantDays" label="空置天数" width="110">
        <template #default="{ row }">
          <span v-if="row.vacantDays > 60" style="color:#f56c6c">
            {{ row.vacantDays }}
          </span>
          <span v-else>{{ row.vacantDays ?? '-' }}</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { houseApi } from '@/api/modules'

const statuses = ['VACANT', 'PENDING_ALLOC', 'ALLOCATED', 'OCCUPIED',
  'MAINTENANCE', 'PENDING_EXIT', 'LOCKED']
const types = ['PUBLIC_RENTAL', 'APARTMENT', 'DORMITORY', 'HOTEL']

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, houseStatus: '', houseType: '' })

function statusTone(s) {
  return ({ OCCUPIED: 'success', ALLOCATED: 'primary', VACANT: 'warning',
    MAINTENANCE: 'info', LOCKED: 'danger' })[s] || 'info'
}

async function load() {
  loading.value = true
  try {
    const data = await houseApi.page({
      pageNum: query.pageNum, pageSize: query.pageSize,
      houseStatus: query.houseStatus || undefined,
      houseType: query.houseType || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}

function reload() { query.pageNum = 1; load() }

onMounted(load)
</script>
'''

F['src/views/Messages.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">消息与待办</h3>
        <el-tag type="danger" size="small" v-if="unread > 0">未读 {{ unread }}</el-tag>
        <div class="spacer" />
        <el-select v-model="query.status" placeholder="状态" clearable
                   style="width:130px" @change="load">
          <el-option label="未读" value="PENDING" />
          <el-option label="已读" value="READ" />
          <el-option label="已办" value="DONE" />
        </el-select>
        <el-button type="primary" @click="load">刷新</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column prop="content" label="内容" min-width="260"
                         show-overflow-tooltip />
        <el-table-column prop="todoType" label="类型" width="110" />
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="priorityTone(row.priority)">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="todoStatus" label="状态" width="100" />
        <el-table-column prop="createTime" label="创建时间" width="170" />
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.todoStatus !== 'PENDING'"
                       @click="markRead(row)">已读</el-button>
            <el-button link type="success" :disabled="row.todoStatus === 'DONE'"
                       @click="markDone(row)">办结</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }" />
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">发送通知</h4>
      <el-form :model="form" label-width="100px" style="max-width:620px">
        <el-form-item label="接收人ID">
          <el-input v-model.number="form.userId" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio value="URGENT">紧急</el-radio>
            <el-radio value="IMPORTANT">重要</el-radio>
            <el-radio value="NORMAL">普通</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="send">创建待办</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { msgApi } from '@/api/modules'
import req from '@/api/request'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const unread = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, status: '' })
const form = reactive({ userId: null, title: '', content: '', priority: 'NORMAL' })

function priorityTone(p) {
  return ({ URGENT: 'danger', IMPORTANT: 'warning' })[p] || 'info'
}

async function load() {
  loading.value = true
  try {
    const data = await msgApi.todos({
      pageNum: query.pageNum, pageSize: query.pageSize,
      userId: auth.user?.userId || undefined,
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
  await req.post(`/messages/todos/${row.id}/read`)
  ElMessage.success('已标记已读')
  load()
}

async function markDone(row) {
  await req.post(`/messages/todos/${row.id}/done`)
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
    await req.post('/messages/todos', { ...form, todoType: 'REMIND' })
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
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个 PC 页面' % count)
