<template>
  <!-- 组织选择：按名称搜索，值仍为组织 ID -->
  <el-select
    :model-value="modelValue"
    filterable
    clearable
    :loading="loading"
    :placeholder="placeholder"
    :style="{ width: width }"
    :data-testid="testid"
    @update:model-value="(v) => emit('update:modelValue', v)"
  >
    <el-option v-for="o in options" :key="o.id" :label="o.orgName" :value="String(o.id)" />
  </el-select>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import req from '@/api/request'

defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '输入组织名称搜索' },
  width: { type: String, default: '100%' },
  testid: { type: String, default: 'org-select' }
})
const emit = defineEmits(['update:modelValue'])

const options = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    options.value = d.rows || d || []
  } catch (e) { options.value = [] } finally { loading.value = false }
})
</script>
