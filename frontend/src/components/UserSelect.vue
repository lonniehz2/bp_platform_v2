<template>
  <!-- 用户选择：按用户名/姓名搜索，值为用户 ID -->
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
    <el-option v-for="u in options" :key="u.id"
               :label="(u.realName || u.username || '') + (u.username ? '（' + u.username + '）' : '')"
               :value="String(u.id)" />
  </el-select>
</template>

<script setup>
import { ref } from 'vue'
import req from '@/api/request'

defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '输入用户名/姓名搜索' },
  width: { type: String, default: '100%' },
  testid: { type: String, default: 'user-select' }
})
const emit = defineEmits(['update:modelValue'])
const options = ref([])
const loading = ref(false)

async function search(keyword) {
  loading.value = true
  try {
    const list = await req.get('/users', { params: { keyword: keyword || undefined } })
    options.value = (Array.isArray(list) ? list : (list.rows || [])).slice(0, 50)
  } catch (e) { options.value = [] } finally { loading.value = false }
}

search('')
</script>
