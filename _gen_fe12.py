# -*- coding: utf-8 -*-
"""补：Sys(审计/字典/参数) + Rbac(用户角色权限) 两个特殊页 + API 封装 + 路由"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

# ==================== 系统支撑页 ====================
F['src/views/SysAdmin.vue'] = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">系统支撑</h3>
      <div class="spacer" />
      <el-button @click="load">刷新</el-button>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="审计日志" name="audit">
        <div class="toolbar">
          <el-select v-model="auditQuery.level" placeholder="级别" clearable
                     style="width:140px" @change="loadAudit">
            <el-option label="CRITICAL" value="CRITICAL" />
            <el-option label="IMPORTANT" value="IMPORTANT" />
            <el-option label="NORMAL" value="NORMAL" />
          </el-select>
          <el-input v-model="auditQuery.operatorName" placeholder="操作人"
                    clearable style="width:150px" @keyup.enter="loadAudit" />
        </div>
        <el-table :data="audits" border size="small" v-loading="loading">
          <el-table-column prop="auditTime" label="时间" width="170" />
          <el-table-column prop="auditType" label="类型" width="110" />
          <el-table-column prop="auditLevel" label="级别" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.auditLevel === 'CRITICAL' ? 'danger'
                : (row.auditLevel === 'IMPORTANT' ? 'warning' : 'info')">
                {{ row.auditLevel }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="action" label="动作" min-width="160" />
          <el-table-column prop="operatorName" label="操作人" width="120" />
          <el-table-column prop="targetType" label="目标方法" min-width="200"
                           show-overflow-tooltip />
        </el-table>
        <div class="muted" style="margin-top:8px">
          审计日志只追加，不提供修改与删除接口
        </div>
      </el-tab-pane>

      <el-tab-pane label="数据字典" name="dict">
        <div class="toolbar">
          <el-select v-model="dictType" style="width:240px" @change="loadDict">
            <el-option v-for="t in dictTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
        <el-table :data="dicts" border size="small">
          <el-table-column prop="dictCode" label="编码" width="200" />
          <el-table-column prop="dictLabel" label="标签" min-width="180" />
          <el-table-column prop="sortNo" label="排序" width="90" />
          <el-table-column prop="dictStatus" label="状态" width="110" />
        </el-table>
        <div class="muted" style="margin-top:8px">
          系统内置 dict_type 的 tenant_id 为空；租户新增同名编码会覆盖内置项
        </div>
      </el-tab-pane>

      <el-tab-pane label="系统参数" name="config">
        <el-table :data="configs" border size="small">
          <el-table-column prop="configKey" label="参数键" width="320" />
          <el-table-column prop="configValue" label="当前值" width="140" />
          <el-table-column prop="valueType" label="类型" width="100" />
          <el-table-column prop="description" label="说明" min-width="240" />
        </el-table>
        <div class="muted" style="margin-top:8px">
          政策参数（公示天数/禁申年限/过渡期/加价倍率）改这里即生效，无需改代码
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { sysApi } from '@/api/modules'

const tab = ref('audit')
const loading = ref(false)
const audits = ref([])
const auditQuery = reactive({ level: '', operatorName: '' })
const dictTypes = ref([])
const dictType = ref('HOUSE_TYPE')
const dicts = ref([])
const configs = ref([])

async function loadAudit() {
  loading.value = true
  try {
    const d = await sysApi.auditLogs({
      pageNum: 1, pageSize: 50,
      level: auditQuery.level || undefined,
      operatorName: auditQuery.operatorName || undefined
    })
    audits.value = d.rows || []
  } finally { loading.value = false }
}

async function loadDictTypes() {
  try { dictTypes.value = await sysApi.dictTypes() } catch (e) { dictTypes.value = [] }
}

async function loadDict() {
  if (!dictType.value) return
  dicts.value = await sysApi.dicts(dictType.value)
}

async function loadConfigs() {
  configs.value = await sysApi.configs()
}

async function load() { loadAudit(); loadDictTypes(); loadDict(); loadConfigs() }
onMounted(load)
</script>
'''

# ==================== RBAC 页 ====================
F['src/views/Rbac.vue'] = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">用户与权限</h3>
      <div class="spacer" />
      <el-button @click="load">刷新</el-button>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="用户" name="users">
        <el-table :data="users" border size="small">
          <el-table-column prop="id" label="ID" width="150" />
          <el-table-column prop="username" label="账号" width="150" />
          <el-table-column prop="realName" label="姓名" width="130" />
          <el-table-column prop="status" label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="isAdmin" label="管理员" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.isAdmin === 1" type="danger" size="small">是</el-tag>
              <span v-else class="muted">否</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="角色" name="roles">
        <el-table :data="roles" border size="small">
          <el-table-column prop="id" label="ID" width="150" />
          <el-table-column prop="roleCode" label="角色编码" width="180" />
          <el-table-column prop="roleName" label="角色名称" min-width="160" />
          <el-table-column prop="status" label="状态" width="110" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="权限项" name="perms">
        <el-table :data="perms" border size="small">
          <el-table-column prop="permCode" label="权限码" width="240" />
          <el-table-column prop="permName" label="名称" min-width="160" />
          <el-table-column prop="permType" label="类型" width="110" />
          <el-table-column prop="status" label="状态" width="110" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-alert type="info" :closable="false" show-icon style="margin-top:12px"
              title="权限校验规则：管理员全放行；普通用户按 permCode 精确匹配；角色或权限被停用后立即失效" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { rbacApi } from '@/api/modules'

const tab = ref('users')
const users = ref([])
const roles = ref([])
const perms = ref([])

async function load() {
  try {
    const u = await rbacApi.users({ pageNum: 1, pageSize: 50 })
    users.value = u.rows || u || []
  } catch (e) { users.value = [] }
  try { roles.value = await rbacApi.roles() } catch (e) { roles.value = [] }
  try { perms.value = await rbacApi.permissions() } catch (e) { perms.value = [] }
}

onMounted(load)
</script>
'''

# ==================== 补齐缺失的 API 封装 ====================
PATCH_API = '''
/** 人员 / 空间（补齐剩余模块） */
export const personApi = {
  page: (params) => req.get('/persons', { params }),
  get: (id) => req.get(`/persons/${id}`)
}

export const spaceApi = {
  page: (params) => req.get('/spaces', { params }),
  get: (id) => req.get(`/spaces/${id}`),
  children: (parentId) => req.get('/spaces/children', { params: { parentId } })
}

/** 退租 / 申诉 / 信用 / 换房 */
export const terminationApi = {
  page: (params) => req.get('/terminations', { params }),
  get: (id) => req.get(`/terminations/${id}`),
  create: (data) => req.post('/terminations', data),
  approve: (id, data) => req.post(`/terminations/${id}/approve`, data)
}

export const appealApi = {
  page: (params) => req.get('/appeals', { params }),
  get: (id) => req.get(`/appeals/${id}`),
  decide: (id, data) => req.post(`/appeals/${id}/decide`, data)
}

export const creditApi = {
  page: (params) => req.get('/credits', { params }),
  penalize: (data) => req.post('/credits/penalties', data),
  restore: (id) => req.post(`/credits/penalties/${id}/restore`)
}

export const exchangeApi = {
  page: (params) => req.get('/exchanges', { params }),
  approve: (id, data) => req.post(`/exchanges/${id}/approve`, data)
}

/** 投诉 / 来访 */
export const complaintApi = {
  page: (params) => req.get('/complaints', { params }),
  handle: (id, data) => req.post(`/complaints/${id}/handle`, data)
}

export const visitApi = {
  page: (params) => req.get('/visits', { params }),
  approve: (id, data) => req.post(`/visits/${id}/approve`, data)
}

/** 短租与日房态 */
export const shortRentApi = {
  page: (params) => req.get('/short-rent-orders', { params }),
  get: (id) => req.get(`/short-rent-orders/${id}`),
  cancel: (id, reason) =>
    req.post(`/short-rent-orders/${id}/cancel`, null, { params: { reason } })
}

export const calendarApi = {
  page: (params) => req.get('/house-calendar', { params }),
  byHouse: (houseId, params) =>
    req.get(`/house-calendar/house/${houseId}`, { params })
}

/** 监管报送 / 开放平台 */
export const govApi = {
  tasks: (params) => req.get('/gov/reports', { params }),
  task: (id) => req.get(`/gov/reports/${id}`),
  details: (id) => req.get(`/gov/reports/${id}/details`),
  submit: (data) => req.post('/gov/reports', data),
  retry: (id) => req.post(`/gov/reports/${id}/retry`),
  stats: () => req.get('/gov/stats'),
  adapters: () => req.get('/gov/adapters')
}

export const openApi = {
  apps: (params) => req.get('/open/apps', { params }),
  createApp: (data) => req.post('/open/apps', data),
  resetSecret: (id) => req.post(`/open/apps/${id}/reset-secret`),
  apis: (params) => req.get('/open/apis', { params }),
  callLogs: (params) => req.get('/open/call-logs', { params }),
  usage: (params) => req.get('/open/usage', { params }),
  hooks: () => req.get('/open/webhooks'),
  verify: (data) => req.post('/open/verify', data)
}

/** RBAC 管理 */
export const rbacApi = {
  users: (params) => req.get('/rbac/users', { params }),
  roles: () => req.get('/rbac/roles'),
  permissions: () => req.get('/rbac/permissions'),
  grant: (data) => req.post('/rbac/user-roles', data)
}
'''

p = os.path.join(BASE, r'src\api\modules.js')
s = io.open(p, encoding='utf-8').read()
if 'personApi' not in s:
    s = s.rstrip() + '\n' + PATCH_API
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ modules.js 追加 14 个模块封装')

for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    print('  + %s' % rel)
