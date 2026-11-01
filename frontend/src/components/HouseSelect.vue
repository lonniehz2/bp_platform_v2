<template>
  <!-- 房源选择：按编号/名称搜索，值仍为房源 ID；选中后抛出完整房源对象 -->
  <el-select
    :model-value="modelValue"
    filterable
    remote
    clearable
    reserve-keyword
    :remote-method="search"
    :loading="loading"
    :placeholder="placeholder || t('contract.houseSearch')"
    :style="{ width: width }"
    :data-testid="testid"
    @update:model-value="onChange"
  >
    <el-option v-for="h in options" :key="h.id" :label="labelOf(h)" :value="String(h.id)">
      <div style="display:flex;justify-content:space-between;gap:12px">
        <span>{{ h.houseName || h.houseCode }}</span>
        <span class="muted" style="font-size:12px">{{ h.houseCode }} · {{ enumLabel('houseStatus', h.houseStatus) }}</span>
      </div>
    </el-option>
    <template #empty>
      <div style="padding:8px;font-size:12px;color:#909399">
        {{ t('contract.houseSearchHint') }}
      </div>
    </template>
  </el-select>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
import { ref, watch } from 'vue'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  orgId: { type: [String, Number], default: '' },
  houseStatus: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  width: { type: String, default: '100%' },
  testid: { type: String, default: 'house-select' }
})
const emit = defineEmits(['update:modelValue', 'picked'])

const options = ref([])
const loading = ref(false)

function labelOf(h) {
  return (h.houseName || h.houseCode) + '（' + (h.houseCode || '') + '）'
}

function onChange(v) {
  emit('update:modelValue', v)
  const hit = options.value.find((h) => String(h.id) === String(v))
  if (hit) emit('picked', hit)
}

async function search(keyword) {
  loading.value = true
  try {
    const d = await req.get('/houses', {
      params: {
        pageNum: 1, pageSize: 30,
        keyword: keyword || undefined,
        orgId: props.orgId || undefined,
        houseStatus: props.houseStatus || undefined
      }
    })
    options.value = d.rows || []
  } catch (e) { options.value = [] } finally { loading.value = false }
}

watch(() => props.orgId, () => { options.value = [] })
</script>
