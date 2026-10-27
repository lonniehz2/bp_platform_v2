<template>
  <!-- 计费项选择：按名称搜索，值为计费项 ID -->
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
    <el-option v-for="x in options" :key="x.id"
               :label="(x.itemName || x.itemCode || '') + (x.unit ? ' · ' + x.unit : '')"
               :value="String(x.id)" />
  </el-select>
</template>

<script setup>
import { ref } from 'vue'
import req from '@/api/request'

defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '输入计费项名称搜索' },
  width: { type: String, default: '100%' },
  testid: { type: String, default: 'fee-item-select' }
})
const emit = defineEmits(['update:modelValue'])
const options = ref([])
const loading = ref(false)

async function search(keyword) {
  loading.value = true
  try {
    const d = await req.get('/fin/fee-items', {
      params: { pageNum: 1, pageSize: 50, keyword: keyword || undefined }
    })
    options.value = d.rows || []
  } catch (e) { options.value = [] } finally { loading.value = false }
}

search('')
</script>
