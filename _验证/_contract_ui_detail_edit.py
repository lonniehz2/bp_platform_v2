# -*- coding: utf-8 -*-
"""合同页：补充表格列 + 详情弹窗 + 编辑弹窗（仅草稿可编辑）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Contracts.vue')

s = io.open(P, encoding='utf-8').read()
changed = []

# 1) 表格补充列（放在「月租」之后）
anchor = '<el-table-column prop="monthlyRent" label="月租" width="95" />'
extra_cols = '''<el-table-column prop="monthlyRent" label="月租" width="95" />
          <el-table-column prop="depositAmount" label="押金" width="95" />
          <el-table-column label="合同类型" width="120">
            <template #default="{ row }">
              {{ row.contractTypeLabel || enumLabel('contractType', row.contractType) }}
            </template>
          </el-table-column>
          <el-table-column prop="signTime" label="签约时间" width="165" />
          <el-table-column label="到期" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.expiringSoon" size="small" type="warning">
                {{ row.daysToExpire }} 天
              </el-tag>
              <span v-else class="muted">—</span>
            </template>
          </el-table-column>'''
if anchor in s and 'prop="depositAmount" label="押金"' not in s:
    s = s.replace(anchor, extra_cols, 1)
    changed.append('表格列')

# 2) 操作列加「详情」「编辑」
op_anchor = '<el-table-column label="操作" width="300" fixed="right">'
if op_anchor in s and 'openContractDetail' not in s:
    s = s.replace(op_anchor,
                  '<el-table-column label="操作" width="380" fixed="right">', 1)
    s = s.replace('<el-table-column label="操作" width="380" fixed="right">\n            <template #default="{ row }">',
                  '''<el-table-column label="操作" width="380" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openContractDetail(row)"
                         data-testid="contract-detail">详情</el-button>
              <el-button link type="warning" :disabled="row.contractStatus !== 'DRAFT'"
                         @click="openContractEdit(row)"
                         data-testid="contract-edit">编辑</el-button>''', 1)
    changed.append('操作列')

# 3) 弹窗（详情 + 编辑）
dialogs = '''
    <!-- 合同详情 -->
    <el-dialog v-model="detailVisible" title="合同详情" width="820px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="合同号">{{ detail.contractNo }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          {{ detail.contractStatusLabel || enumLabel('contractStatus', detail.contractStatus) }}
        </el-descriptions-item>
        <el-descriptions-item label="合同类型">
          {{ detail.contractTypeLabel || enumLabel('contractType', detail.contractType) }}
        </el-descriptions-item>
        <el-descriptions-item label="承租人">{{ detail.lesseeName }}</el-descriptions-item>
        <el-descriptions-item label="证件号">{{ detail.lesseeIdCardMask }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detail.lesseePhone }}</el-descriptions-item>
        <el-descriptions-item label="房屋" :span="2">{{ detail.houseAddress }}</el-descriptions-item>
        <el-descriptions-item label="面积">{{ detail.houseArea }} ㎡</el-descriptions-item>
        <el-descriptions-item label="出租方">{{ detail.lessorOrgIdName }}</el-descriptions-item>
        <el-descriptions-item label="起租">{{ detail.leaseStart }}</el-descriptions-item>
        <el-descriptions-item label="止租">{{ detail.leaseEnd }}</el-descriptions-item>
        <el-descriptions-item label="租期">{{ detail.leaseMonths }} 个月</el-descriptions-item>
        <el-descriptions-item label="月租">{{ detail.monthlyRent }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ detail.depositAmount }}</el-descriptions-item>
        <el-descriptions-item label="已收">{{ detail.actualPay }}</el-descriptions-item>
        <el-descriptions-item label="补贴">{{ detail.subsidyAmount }}</el-descriptions-item>
        <el-descriptions-item label="支付周期">{{ detail.payCycle }}</el-descriptions-item>
        <el-descriptions-item label="签约时间">{{ detail.signTime }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detail.remark || '—' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer><el-button @click="detailVisible = false">关闭</el-button></template>
    </el-dialog>

    <!-- 编辑合同（仅草稿） -->
    <el-dialog v-model="editVisible" title="编辑合同条款（仅草稿可改）" width="620px">
      <el-alert type="warning" :closable="false" show-icon
                title="签约后修改金额或租期请走「合同变更」，此处仅限草稿" />
      <el-form :model="ef" label-width="100px" style="margin-top:12px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="月租">
            <el-input v-model="ef.monthlyRent" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="押金">
            <el-input v-model="ef.depositAmount" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="起租日">
            <el-date-picker v-model="ef.leaseStart" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="止租日">
            <el-date-picker v-model="ef.leaseEnd" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="支付周期">
            <el-select v-model="ef.payCycle" style="width:100%">
              <el-option label="月付" value="MONTH" />
              <el-option label="季付" value="QUARTER" />
              <el-option label="半年付" value="HALF_YEAR" />
              <el-option label="年付" value="YEAR" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="每月付款日">
            <el-input v-model="ef.payDay" type="number" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="ef.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveContractEdit">保存</el-button>
      </template>
    </el-dialog>
'''
if 'detailVisible' not in s:
    idx = s.rfind('</template>')
    s = s[:idx] + dialogs + s[idx:]
    changed.append('弹窗')

# 4) 脚本逻辑
script = '''
/** 合同详情 / 编辑 */
const detailVisible = ref(false)
const detail = ref({})
const editVisible = ref(false)
const editingId = ref(null)
const ef = reactive({ monthlyRent: null, depositAmount: null, leaseStart: '', leaseEnd: '',
  payCycle: 'MONTH', payDay: 5, remark: '' })

async function openContractDetail(row) {
  // 列表已有大部分字段，再取一次详情确保完整
  try {
    const d = await req.get(`/contracts/${row.id}`)
    detail.value = d || row
  } catch (e) { detail.value = row }
  detailVisible.value = true
}

function openContractEdit(row) {
  editingId.value = row.id
  ef.monthlyRent = Number(row.monthlyRent || 0)
  ef.depositAmount = Number(row.depositAmount || 0)
  ef.leaseStart = row.leaseStart || ''
  ef.leaseEnd = row.leaseEnd || ''
  ef.payCycle = row.payCycle || 'MONTH'
  ef.payDay = Number(row.payDay || 5)
  ef.remark = row.remark || ''
  editVisible.value = true
}

async function saveContractEdit() {
  saving.value = true
  try {
    await req.put(`/contracts/${editingId.value}`, { ...ef })
    ElMessage.success('合同条款已更新')
    editVisible.value = false
    load()
  } finally { saving.value = false }
}
'''
if 'async function openContractDetail' not in s:
    anchor2 = 'onMounted(load)'
    if anchor2 in s:
        s = s.replace(anchor2, script + '\n' + anchor2, 1)
        changed.append('脚本')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Contracts.vue 改动：', '、'.join(changed) if changed else '（无）')
