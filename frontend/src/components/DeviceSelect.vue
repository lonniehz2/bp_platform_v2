<template>
  <!-- 设备选择：按设备编号/MAC/名称搜索 -->
  <el-select
    :model-value="modelValue"
    filterable
    remote
    clearable
    reserve-keyword
    :remote-method="search"
    :loading="loading"
    :placeholder="placeholder"
    :style="{ width: width }"
    :data-testid="testid"
    @update:model-value="(v) => emit('update:modelValue', v)"
  >
    <el-option v-for="d in options" :key="d.deviceId"
               :label="(d.deviceName || d.deviceId) + '（' + (d.deviceId || '') + '）'"
               :value="d.deviceId" />
  </el-select>
</template>

<script setup>
import { ref } from 'vue'
import req from '@/api/request'

defineProps({
  modelValue: { type: [String, Number], default: '' },
  deviceType: { type: String, default: '' },
  placeholder: { type: String, default: '输入设备编号/名称搜索' },
  width: { type: String, default: '100%' },
  testid: { type: String, default: 'device-select' }
})
const emit = defineEmits(['update:modelValue'])
const options = ref([])
const loading = ref(false)

async function search(keyword) {
  loading.value = true
  try {
    const d = await req.get('/devices', {
      params: { pageNum: 1, pageSize: 50, keyword: keyword || undefined }
    })
    options.value = d.rows || []
  } catch (e) { options.value = [] } finally { loading.value = false }
}

search('')
</script>
