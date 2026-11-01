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
    :placeholder="placeholderText"
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
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import req from '@/api/request'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  deviceType: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  width: { type: String, default: '100%' },
  testid: { type: String, default: 'device-select' }
})
const emit = defineEmits(['update:modelValue'])
const placeholderText = computed(() => props.placeholder || t('device.searchHint'))
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
