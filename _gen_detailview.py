# -*- coding: utf-8 -*-
"""生成字段中文字典 + 通用详情组件"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'
V = os.path.join(FE, 'views')

# ---------- 1) 从现有表格提取字段中文名 ----------
FIELD = {}
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    for m in re.finditer(r'prop="(\w+)"\s+label="([^"]+)"', s):
        FIELD.setdefault(m.group(1), m.group(2))

# 补充通用/系统字段（表格里没出现的）
EXTRA = {
    'id': 'ID', 'tenantId': '租户', 'orgId': '所属组织', 'orgName': '组织名称',
    'createBy': '创建人', 'createTime': '创建时间', 'updateBy': '更新人',
    'updateTime': '更新时间', 'isDeleted': '是否删除', 'version': '版本',
    'remark': '备注', 'status': '状态', 'sortNo': '排序',
    'personId': '人员', 'personName': '人员姓名',
    'houseId': '房源', 'houseName': '房源名称', 'houseCode': '房源编号',
    'spaceId': '空间', 'spaceName': '空间名称',
    'contractId': '合同', 'contractNo': '合同号',
    'billId': '账单', 'billNo': '账单号',
    'amount': '金额', 'totalAmount': '总金额', 'payableAmount': '应付金额',
    'paidAmount': '已缴金额', 'depositAmount': '押金金额',
    'monthlyRent': '月租金', 'rentPrice': '租金单价',
    'dueDate': '缴费截止日', 'billPeriod': '账期',
    'startDate': '开始日期', 'endDate': '结束日期',
    'effectiveDate': '生效日期', 'expireDate': '失效日期',
    'reason': '原因', 'content': '内容', 'title': '标题',
    'type': '类型', 'level': '级别', 'channel': '渠道',
    'batchNo': '批次号', 'batchName': '批次名称',
    'applicationNo': '申请编号', 'allocationNo': '配租单号',
    'terminationNo': '退租单号', 'reviewNo': '年审单号',
    'refundNo': '退款单号', 'recordNo': '单据号',
    'publicityNo': '公示号', 'complaintNo': '投诉单号',
    'appealNo': '申诉单号', 'exchangeNo': '换房单号',
    'workOrderNo': '工单号', 'keyringNo': '钥匙包编号',
}

LABELS = dict(EXTRA)
LABELS.update({k: v for k, v in FIELD.items() if k not in LABELS})
# 已存在的中文优先用表格里的
LABELS.update(FIELD)

lines = ',\n'.join("  %s: '%s'" % (k, v.replace("'", "\\'"))
                   for k, v in sorted(LABELS.items()))
src = '''/**
 * 字段名 → 中文名（详情展示用）。
 *
 * 来源：从各页面表格的 prop/label 自动提取（205 个），
 * 再补充表格里没出现但接口会返回的通用字段。
 * 新增字段时在这里加一行即可，无需改页面。
 */
export const FIELD_LABEL = {
%s
}

/** 系统/内部字段：默认折叠，避免干扰业务阅读 */
export const INTERNAL_FIELDS = new Set([
  'id', 'tenantId', 'createBy', 'createTime', 'updateBy', 'updateTime',
  'isDeleted', 'version', 'orgPath', 'spacePath', 'pathCode', 'orgLevel',
  'spaceLevel', 'remark'
])

export function fieldLabel(key) {
  return FIELD_LABEL[key] || key
}
''' % lines

io.open(os.path.join(FE, 'constants', 'fieldLabels.js'), 'w',
        encoding='utf-8').write(src)
print('  ✓ constants/fieldLabels.js（%d 个字段中文名）' % len(LABELS))

# ---------- 2) 通用详情组件 ----------
COMP = '''<template>
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
import { fieldLabel, INTERNAL_FIELDS } from '@/constants/fieldLabels'
import { enumLabel } from '@/constants/enums'

const props = defineProps({
  row: { type: Object, default: () => ({}) },
  columns: { type: Number, default: 2 }
})

const showRaw = ref(false)
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
  return v.replace('T', ' ').replace(/\\.\\d+$/, '')
}

function build(key, value) {
  const label = fieldLabel(key)
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
  const row = props.row || {}
  return Object.keys(row)
    .filter((k) => !k.endsWith('Label') && !k.endsWith('Name'))
    .filter((k) => !INTERNAL_FIELDS.has(k))
    .filter((k) => !Array.isArray(row[k]) || row[k].length)
    .map((k) => build(k, row[k]))
    .filter((f) => f.text !== '（对象）')
})

const internalFields = computed(() => {
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
'''
os.makedirs(os.path.join(FE, 'components'), exist_ok=True)
io.open(os.path.join(FE, 'components', 'DetailView.vue'), 'w',
        encoding='utf-8').write(COMP)
print('  ✓ components/DetailView.vue')
