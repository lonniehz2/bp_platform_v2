<template>
  <!--
    人员选择器（远程搜索）

    为什么不用普通下拉：人员量级上万，一次性加载既慢又没法找。
    这里在输入关键字后才请求服务端（/persons?keyword=），只取前 20 条；
    同时保留「直接粘贴 ID」的能力，方便从其他系统带过来的人。
  -->
  <el-select
    :model-value="modelValue"
    filterable
    remote
    reserve-keyword
    clearable
    :remote-method="search"
    :loading="loading"
    :placeholder="placeholder"
    :style="{ width: width }"
    :data-testid="testid"
    @update:model-value="(v) => emit('update:modelValue', v)"
  >
    <el-option
      v-for="p in options"
      :key="p.id"
      :label="labelOf(p)"
      :value="String(p.id)"
    >
      <div style="display:flex;justify-content:space-between;gap:12px">
        <span>{{ p.personName }}</span>
        <span class="muted" style="font-size:12px">{{ p.phoneMask || p.idCardMask || '' }}</span>
      </div>
    </el-option>
    <template #empty>
      <div style="padding:8px;font-size:12px;color:#909399">
        输入姓名 / 手机 / 证件号搜索；也可直接粘贴 19 位人员ID
      </div>
    </template>
  </el-select>
</template>

<script setup>
import { ref, watch } from 'vue'
import req from '@/api/request'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '输入姓名/手机/证件号搜索' },
  width: { type: String, default: '240px' },
  testid: { type: String, default: 'person-picker' }
})
const emit = defineEmits(['update:modelValue'])

const options = ref([])
const loading = ref(false)
let seq = 0

function labelOf(p) {
  return p.personName || p.id
}

async function search(keyword) {
  const k = (keyword || '').trim()
  // 纯数字且长度 ≥ 15：当作人员ID直接匹配，不打扰服务端模糊搜索
  if (/^\d{15,}$/.test(k)) {
    loading.value = true
    try {
      const d = await req.get('/persons', { params: { pageNum: 1, pageSize: 5, keyword: k } })
      options.value = d.rows || []
    } catch (e) { options.value = [] } finally { loading.value = false }
    return
  }
  if (!k) { options.value = []; return }
  const mine = ++seq
  loading.value = true
  try {
    const d = await req.get('/persons', { params: { pageNum: 1, pageSize: 20, keyword: k } })
    if (mine === seq) options.value = d.rows || []
  } catch (e) {
    if (mine === seq) options.value = []
  } finally {
    if (mine === seq) loading.value = false
  }
}

// 回填：外部传入已有 ID 时，取一次详情用于显示姓名
watch(() => props.modelValue, async (v) => {
  if (!v || options.value.some((o) => String(o.id) === String(v))) return
  try {
    const d = await req.get('/persons', { params: { pageNum: 1, pageSize: 5, keyword: String(v) } })
    const hit = (d.rows || []).find((o) => String(o.id) === String(v))
    if (hit) options.value = [hit, ...options.value]
  } catch (e) { /* 忽略：仅影响显示 */ }
}, { immediate: true })
</script>
