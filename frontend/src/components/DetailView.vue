<template>
  <div class="detail-view">
    <el-descriptions :column="columns" border size="small">
      <el-descriptions-item v-for="f in mainFields" :key="f.key" :label="f.label"
                            :label-class-name="f.wide ? 'wide-label' : ''">
        <el-tag v-if="f.kind === 'tag'" size="small" :type="f.tagType">{{ f.text }}</el-tag>
        <span v-else-if="f.kind === 'money'" class="money">{{ f.text }}</span>
        <span v-else-if="f.kind === 'muted'" class="muted">{{ f.text }}</span>
        <span v-else>{{ f.text }}</span>
      </el-descriptions-item>
    </el-descriptions>

    <el-empty v-if="!mainFields.length" description="无字段可展示" :image-size="50" />

    <el-collapse v-if="internalFields.length" class="internal">
      <el-collapse-item :title="`系统字段（${internalFields.length}）`" name="internal">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item v-for="f in internalFields" :key="f.key" :label="f.label">
            <span class="muted">{{ f.text }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-collapse-item>
    </el-collapse>

    <div class="raw-toggle">
      <el-button link type="primary" @click="showRaw = !showRaw">
        {{ showRaw ? '收起原始数据' : '查看原始数据（排查用）' }}
      </el-button>
    </div>
    <pre v-if="showRaw" class="raw">{{ pretty }}</pre>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { labelOf, INTERNAL_FIELDS, loadRemoteLabels } from '@/constants/fieldLabels'
import { onMounted, ref as vueRef } from 'vue'
import request from '@/api/request'
import { enumLabel } from '@/constants/enums'

const props = defineProps({
  row: { type: Object, default: () => ({}) },
  columns: { type: Number, default: 2 }
})

const showRaw = ref(false)
const labelVersion = ref(0)

onMounted(async () => {
  await loadRemoteLabels(() => request.get('/sys/field-labels'))
  labelVersion.value++   // 触发字段标签重算
})
const pretty = computed(() => JSON.stringify(props.row || {}, null, 2))

/** 枚举类字段（显示为中文标签） */
const ENUM_KEY = /(Status|Type|Stage|Mode|Level|Channel|Result|Source|Kind|Category)$/
/** 金额类字段 */
const MONEY_KEY = /(Amount|Price|Rent|Fee|Deposit|Balance|Arrears)$/

function isBlank(v) {
  return v === null || v === undefined || v === ''
}

function fmtDate(v) {
  if (typeof v !== 'string') return v
  // 后端可能是 ISO（2026-10-20T22:17:13）
  return v.replace('T', ' ').replace(/\.\d+$/, '')
}

function build(key, value) {
  const label = labelOf(key)
  const base = { key, label }

  if (isBlank(value)) {
    return { ...base, text: '-', kind: 'muted' }
  }
  // 后端已补的中文标签优先
  const labelValue = props.row[key + 'Label']
  const nameValue = props.row[key + 'Name']

  if (Array.isArray(value)) {
    if (value.length && typeof value[0] === 'object') {
      return { ...base, text: `${value.length} 条明细`, kind: 'muted' }
    }
    return { ...base, text: value.join('、') || '-', kind: '' }
  }
  if (typeof value === 'object') {
    return { ...base, text: '（对象）', kind: 'muted' }
  }
  if (typeof value === 'boolean') {
    return { ...base, text: value ? '是' : '否', kind: '' }
  }
  if (key === 'id' || /Id$/.test(key)) {
    // 有名称就显示名称，否则显示编号（等宽小字）
    if (nameValue) return { ...base, text: nameValue, kind: '' }
    return { ...base, text: String(value), kind: 'muted' }
  }
  if (ENUM_KEY.test(key)) {
    const text = labelValue || enumLabel(key, value)
    const good = ['ENABLED', 'ACTIVE', 'PAID', 'EFFECTIVE', 'SUCCESS', 'APPROVED',
      'NORMAL', 'ONLINE', 'PASS', 'COMPLETED', 'RESOLVED'].includes(String(value))
    const bad = ['FAILED', 'REJECTED', 'OVERDUE', 'ABNORMAL', 'FROZEN', 'CRITICAL',
      'SEVERE', 'EXPIRED', 'OFFLINE'].includes(String(value))
    return { ...base, text, kind: 'tag', tagType: good ? 'success' : (bad ? 'danger' : 'info') }
  }
  if (MONEY_KEY.test(key) && !Number.isNaN(Number(value))) {
    return { ...base, text: '¥ ' + Number(value).toFixed(2), kind: 'money' }
  }
  if (typeof value === 'string' && /Time$|Date$/.test(key)) {
    return { ...base, text: fmtDate(value), kind: '' }
  }
  if (typeof value === 'string' && value.length > 120) {
    return { ...base, text: value, kind: '', wide: true }
  }
  return { ...base, text: String(value), kind: '' }
}

const mainFields = computed(() => {
  void labelVersion.value
  const row = props.row || {}
  return Object.keys(row)
    .filter((k) => !k.endsWith('Label') && !k.endsWith('Name'))
    .filter((k) => !INTERNAL_FIELDS.has(k))
    .filter((k) => !Array.isArray(row[k]) || row[k].length)
    .map((k) => build(k, row[k]))
    .filter((f) => f.text !== '（对象）')
})

const internalFields = computed(() => {
  void labelVersion.value
  const row = props.row || {}
  return Object.keys(row)
    .filter((k) => INTERNAL_FIELDS.has(k))
    .map((k) => build(k, row[k]))
})
</script>

<style scoped>
.detail-view :deep(.el-descriptions__label) { width: 130px; white-space: nowrap; }
.detail-view :deep(.el-descriptions__content) { word-break: break-all; }
.money { color: #f56c6c; font-weight: 600; }
.muted { color: #909399; font-size: 12px; }
.internal { margin-top: 12px; }
.raw-toggle { margin-top: 8px; }
.raw { max-height: 300px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
