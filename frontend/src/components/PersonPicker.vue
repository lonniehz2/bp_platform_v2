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
  placeholder: { type: String, default: '输入姓名/手机/身份证号/人员ID 搜索' },
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
  const type = classify(k)
  if (!k) { options.value = []; return }
  const mine = ++seq
  loading.value = true
  try {
    let d
    if (type === 'ID') {
      // 19 位及以上：按人员ID精确取详情（列表接口不按 ID 模糊匹配）
      d = await req.get(`/persons/${k}`).then((p) => ({ rows: p ? [p] : [] })).catch(() => ({ rows: [] }))
    } else {
      // 18 位身份证 / 11 位手机号 / 姓名，都走关键字（后端已支持这三类字段）
      d = await req.get('/persons', { params: { pageNum: 1, pageSize: 20, keyword: k } })
    }
    if (mine === seq) options.value = d.rows || []
  } catch (e) {
    if (mine === seq) options.value = []
  } finally {
    if (mine === seq) loading.value = false
  }
}

/**
 * 按输入形态分流（避免「18 位身份证」被当成人员 ID）：
 *   19 位及以上纯数字 → 人员 ID
 *   18 位（17 位数字 + 数字或 X）→ 身份证号
 *   11 位纯数字 → 手机号
 *   其余 → 姓名/关键字
 */
function classify(k) {
  if (/^\d{19,}$/.test(k)) return 'ID'
  if (/^\d{17}[\dXx]$/.test(k)) return 'IDCARD'
  if (/^\d{11}$/.test(k)) return 'PHONE'
  return 'NAME'
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
