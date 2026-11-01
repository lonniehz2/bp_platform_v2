<template>
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
        <el-icon><Upload /></el-icon>{{ t('common.upload') }}
      </el-button>
    </el-upload>

    <div class="files">
      <div v-for="f in files" :key="f.id" class="file-item">
        <el-icon><Document /></el-icon>
        <a :href="downloadUrl(f.id)" target="_blank">{{ f.fileName }}</a>
        <span class="muted">{{ (f.fileSize / 1024).toFixed(0) }} KB</span>
        <el-button link type="danger" size="small" @click="remove(f)">{{ t('common.delete') }}</el-button>
      </div>
      <div v-if="!files.length" class="muted">{{ t('common.noFiles') }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import req, { getToken, getTenant } from '@/api/request'

const { t } = useI18n()

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
  const ok = /^(image\/(jpeg|png|gif|webp|bmp))$|^application\/pdf$/.test(file.type)
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
