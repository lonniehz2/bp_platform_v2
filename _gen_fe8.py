# -*- coding: utf-8 -*-
"""前端补全：上传组件 + 房源状态变更 + 4 个新页面 + 分包"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

# ==================== 上传组件 ====================
F['src/components/FileUploader.vue'] = '''<template>
  <div class="uploader">
    <el-upload
      :action="action"
      :headers="headers"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :on-success="onSuccess"
      :on-error="onError"
      name="file"
    >
      <el-button size="small" :loading="loading">
        <el-icon><Upload /></el-icon>上传附件
      </el-button>
    </el-upload>

    <div class="files">
      <div v-for="f in files" :key="f.id" class="file-item">
        <el-icon><Document /></el-icon>
        <a :href="downloadUrl(f.id)" target="_blank">{{ f.fileName }}</a>
        <span class="muted">{{ (f.fileSize / 1024).toFixed(0) }} KB</span>
        <el-button link type="danger" size="small" @click="remove(f)">删除</el-button>
      </div>
      <div v-if="!files.length" class="muted">暂无附件（支持 jpg/png/pdf，≤10MB）</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req, { getToken, getTenant } from '@/api/request'

const props = defineProps({
  bizType: { type: String, required: true },
  bizId: { type: [Number, String], default: null }
})

const loading = ref(false)
const files = ref([])

const action = computed(() =>
  `/api/v1/files/upload?bizType=${props.bizType}` +
  (props.bizId ? `&bizId=${props.bizId}` : ''))

// el-upload 需要 headers 传不透明令牌与租户
const headers = computed(() => ({
  Authorization: `Bearer ${getToken()}`,
  'X-Tenant-Id': getTenant()
}))

function downloadUrl(id) { return `/api/v1/files/${id}/download` }

function beforeUpload(file) {
  const ok = /^(image\\/(jpeg|png|gif|webp|bmp))$|^application\\/pdf$/.test(file.type)
  if (!ok) {
    ElMessage.error('仅支持图片或 PDF')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件不能超过 10MB')
    return false
  }
  loading.value = true
  return true
}

function onSuccess(resp) {
  loading.value = false
  if (resp.code === 'BP00000') {
    ElMessage.success('上传成功')
    files.value.unshift(resp.data)
  } else {
    ElMessage.error(resp.message || '上传失败')
  }
}

function onError() {
  loading.value = false
  ElMessage.error('上传失败（检查登录状态与文件大小）')
}

async function remove(f) {
  await req.post(`/files/${f.id}/remove`)
  files.value = files.value.filter((x) => x.id !== f.id)
  ElMessage.success('已删除')
}

async function load() {
  if (!props.bizId) return
  try {
    files.value = await req.get('/files', {
      params: { bizType: props.bizType, bizId: props.bizId }
    }) || []
  } catch (e) { files.value = [] }
}

watch(() => props.bizId, load)
onMounted(load)
</script>

<style scoped>
.uploader { display: flex; flex-direction: column; gap: 8px; }
.files { display: flex; flex-direction: column; gap: 6px; }
.file-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.file-item a { color: #409eff; text-decoration: none; }
</style>
'''

# ==================== 房源：补状态变更 ====================
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
        <el-option v-for="t in houseTypeOptions" :key="t.value"
                   :label="t.label" :value="t.value" />
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
      <el-table-column prop="vacantDays" label="空置天数" width="100">
        <template #default="{ row }">
          <span v-if="row.vacantDays > 60" style="color:#f56c6c">{{ row.vacantDays }}</span>
          <span v-else>{{ row.vacantDays ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openStatus(row)">变更状态</el-button>
          <el-button link @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <!-- 状态变更：闭环「写入」能力 -->
    <el-dialog v-model="statusVisible" title="变更房源状态" width="440px">
      <el-alert type="warning" :closable="false" show-icon
                title="状态跃迁受后端状态机约束，非法跃迁会被拒绝" />
      <el-form :model="statusForm" label-width="90px" style="margin-top:12px">
        <el-form-item label="当前状态">
          <el-input :model-value="current?.houseStatusLabel || current?.houseStatus"
                    disabled />
        </el-form-item>
        <el-form-item label="目标状态">
          <el-select v-model="statusForm.targetStatus" style="width:100%">
            <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="statusForm.reason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doStatus">确认变更</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="房源详情" size="480px">
      <el-descriptions v-if="detail" :column="1" border size="small">
        <el-descriptions-item label="编号">{{ detail.houseCode }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ detail.houseName }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ detail.houseType }}</el-descriptions-item>
        <el-descriptions-item label="面积">{{ detail.area }} ㎡</el-descriptions-item>
        <el-descriptions-item label="户型">{{ detail.unitLayout }}</el-descriptions-item>
        <el-descriptions-item label="朝向">{{ detail.orientation }}</el-descriptions-item>
        <el-descriptions-item label="楼层">{{ detail.floorNo }}</el-descriptions-item>
        <el-descriptions-item label="租金标准">{{ detail.rentStandard }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ detail.houseStatusLabel }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top:16px">
        <h4 style="margin:0 0 8px">房源附件</h4>
        <FileUploader biz-type="HOUSE" :biz-id="detail?.id" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { houseApi } from '@/api/modules'
import { useDict } from '@/composables/useDict'
import FileUploader from '@/components/FileUploader.vue'

// 房源状态来自后端枚举（无独立字典项），类型走系统字典 HOUSE_TYPE
const statuses = ['VACANT', 'PENDING_ALLOC', 'ALLOCATED', 'OCCUPIED',
  'MAINTENANCE', 'PENDING_EXIT', 'LOCKED']
const { options: houseTypeOptions } = useDict('HOUSE_TYPE', [
  { value: 'PUBLIC_RENTAL', label: '公租房' },
  { value: 'APARTMENT', label: '公寓' },
  { value: 'DORMITORY', label: '宿舍' },
  { value: 'HOTEL', label: '酒店/民宿' }
])

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, houseStatus: '', houseType: '' })

const statusVisible = ref(false)
const current = ref(null)
const statusForm = reactive({ targetStatus: '', reason: '' })
const detailVisible = ref(false)
const detail = ref(null)

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

function openStatus(row) {
  current.value = row
  statusForm.targetStatus = ''
  statusForm.reason = ''
  statusVisible.value = true
}

async function doStatus() {
  if (!statusForm.targetStatus) {
    ElMessage.warning('请选择目标状态')
    return
  }
  saving.value = true
  try {
    await houseApi.setStatus(current.value.id, { ...statusForm })
    ElMessage.success('状态已变更')
    statusVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function openDetail(row) {
  detail.value = await houseApi.get(row.id)
  detailVisible.value = true
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
print('生成 %d 个文件（上传组件 + 房源写入）' % count)
