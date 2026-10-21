# -*- coding: utf-8 -*-
"""前端：表单必填校验 + 修正公示结束路径 + 设备页按真实字段"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'
VIEWS = os.path.join(FE, 'views')

# ==================== 1) modules.js：公示 finish → close ====================
p = os.path.join(FE, 'api', 'modules.js')
s = io.open(p, encoding='utf-8').read()
s = s.replace(
    "  finish: (id) => req.post(`/publicities/${id}/finish`)",
    "  // 后端真实动作是 close（结束公示）/ publish（发布），无 finish\n"
    "  publish: (id) => req.post(`/publicities/${id}/publish`),\n"
    "  close: (id, remark) => req.post(`/publicities/${id}/close`, { remark }),\n"
    "  finish: (id, remark) => req.post(`/publicities/${id}/close`, { remark })")
# 设备：接口已补齐，去掉“已知缺口”注释
s = s.replace(
    """  // ⚠️ 已知缺口：后端目前只有「门锁绑定解析」，没有设备列表接口。
  // 保留占位，联调时若 404 属预期，需后端补 DeviceController 后再接。
  devices: (params) => req.get('/devices', { params }),""",
    """  // 设备列表接口已由 DeviceController 补齐（GET /api/v1/devices）
  devices: (params) => req.get('/devices', { params }),
  deviceStats: () => req.get('/devices/stats'),""")
io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ modules.js：公示改为 close/publish，设备接口去掉缺口标记')

# ==================== 2) 表单必填校验（12 个生成页） ====================
# 按后端 Cmd 的 @NotNull 语义确定必填字段
REQUIRED = {
    'Terminations': ['personId', 'contractId', 'terminationType', 'planExitDate'],
    'Appeals': ['bizType', 'bizId', 'personId', 'appealReason'],
    'Credits': ['personId', 'violationType', 'sanctionType'],
    'Exchanges': ['personId', 'oldContractId', 'newHouseId'],
    'Complaints': ['complaintType', 'title', 'content'],
    'Visits': ['visitType'],
    'GovReport': ['targetSystem', 'reportType'],
    'OpenApps': ['appName', 'appType'],
}

PAGES = ['Persons', 'Spaces', 'Terminations', 'Appeals', 'Credits', 'Exchanges',
         'Complaints', 'Visits', 'ShortRent', 'HouseCalendar', 'GovReport', 'OpenApps']

patched = 0
for page in PAGES:
    fp = os.path.join(VIEWS, page + '.vue')
    src = io.open(fp, encoding='utf-8').read()
    if 'validateForm' in src:
        continue

    # 在 submit() 开头插入校验
    old_submit = '''async function submit() {
  saving.value = true'''
    new_submit = '''/** 必填校验（字段级，依赖后端 Cmd 的 @NotNull 语义）。 */
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
  saving.value = true'''

    if old_submit in src:
        src = src.replace(old_submit, new_submit, 1)

    # 注入 REQUIRED 常量（放在 fields 之后）
    anchor = "const model = reactive({})"
    if anchor in src:
        req_list = REQUIRED.get(page, [])
        src = src.replace(
            anchor,
            anchor + '\n\n// 必填字段（取自后端 Cmd 的 @NotNull）\nconst REQUIRED = [%s]'
            % ', '.join("'%s'" % k for k in req_list), 1)

    io.open(fp, 'w', encoding='utf-8').write(src)
    patched += 1

print('  ✓ 为 %d 个页面加了必填/数字校验' % patched)

# ==================== 3) 设备页按真实字段 ====================
dfs = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">设备管理</h3>
      <el-tag size="small" type="info">
        在线 {{ stats.online ?? 0 }} / 共 {{ stats.total ?? 0 }}
        （{{ stats.onlineRate ?? 0 }}%）
      </el-tag>
      <div class="spacer" />
      <el-input v-model.number="query.spaceId" placeholder="空间ID" clearable
                style="width:150px" @keyup.enter="load" />
      <el-select v-model="query.onlineStatus" placeholder="在线状态" clearable
                 style="width:130px" @change="load">
        <el-option label="在线" :value="1" />
        <el-option label="离线" :value="0" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="设备表按空间关联（无 houseId/lockId 列）；门锁与房源关系由绑定记录推导"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="deviceId" label="设备ID" width="200" />
      <el-table-column prop="deviceName" label="设备名称" min-width="150" />
      <el-table-column prop="deviceType" label="类型" width="120" />
      <el-table-column prop="deviceMac" label="MAC" width="160" />
      <el-table-column prop="spaceId" label="空间" width="140" />
      <el-table-column prop="onlineStatus" label="在线" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.onlineStatus === 1 ? 'success' : 'info'">
            {{ row.onlineStatus === 1 ? '在线' : '离线' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="battery" label="电量" width="90">
        <template #default="{ row }">
          <span v-if="row.battery != null && row.battery < 20"
                style="color:#f56c6c">{{ row.battery }}%</span>
          <span v-else>{{ row.battery ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="deviceStatus" label="状态" width="110" />
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { devApi } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const stats = ref({})
const query = reactive({ pageNum: 1, pageSize: 20, spaceId: '', onlineStatus: '' })

async function load() {
  loading.value = true
  try {
    const data = await devApi.devices({
      pageNum: query.pageNum, pageSize: query.pageSize,
      spaceId: query.spaceId || undefined,
      onlineStatus: query.onlineStatus === '' ? undefined : query.onlineStatus
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
    stats.value = await devApi.deviceStats()
  } catch (e) { rows.value = [] } finally { loading.value = false }
}

onMounted(load)
</script>
'''
io.open(os.path.join(VIEWS, 'Devices.vue'), 'w', encoding='utf-8').write(dfs)
print('  ✓ Devices.vue 重写（按真实字段 + 在线率统计）')
