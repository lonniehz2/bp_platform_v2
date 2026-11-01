<template>
  <!-- 合同选择：按合同号/承租人搜索，值为合同 ID -->
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
    <el-option v-for="x in options" :key="x.id"
               :label="(x.contractNo || '') + ' · ' + (x.lesseeName || '')"
               :value="String(x.id)" />
  </el-select>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import req from '@/api/request'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  width: { type: String, default: '100%' },
  testid: { type: String, default: 'contract-select' }
})
const emit = defineEmits(['update:modelValue'])
const placeholderText = computed(() => props.placeholder || t('contract.searchHint'))
const options = ref([])
const loading = ref(false)

async function search(keyword) {
  loading.value = true
  try {
    const d = await req.get('/contracts', { params: { pageNum: 1, pageSize: 30, keyword: keyword || undefined } })
    options.value = d.rows || []
  } catch (e) { options.value = [] } finally { loading.value = false }
}
</script>
