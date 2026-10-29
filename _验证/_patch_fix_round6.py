# -*- coding: utf-8 -*-
"""账单选择/批量出账选项；押金双向自动带出。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return s


# ================= Bills =================
p = os.path.join(V, 'Bills.vue')
patch(p, [
    ('''      <el-table :data="rows" @selection-change="(v) => (selected = v)"''',
     '''      <el-table :data="rows" @selection-change="onSelect"''', '选择事件'),
    ('''        <el-button type="success" @click="genVisible = true">批量出账</el-button>''',
     '''        <el-button type="success" @click="openGen">批量出账</el-button>''', '打开出账'),
    ('''  if (!selected.length) { ElMessage.warning('请先勾选账单'); return }
  for (const row of selected) {''',
     '''  const rows = selected.value
  if (!rows.length) { ElMessage.warning('请先勾选账单'); return }
  for (const row of rows) {''', '批量催缴取值'),
])

s = io.open(p, encoding='utf-8').read()
if 'function onSelect' not in s:
    s = s.replace('''const selected = ref([])''', '''const selected = ref([])

function onSelect(v) { selected.value = v || [] }

async function loadGenOptions() {
  try {
    const org = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = (org && org.rows) || []
  } catch (e) { orgOptions.value = [] }
  try {
    const fi = await req.get('/fin/fee-items', { params: { pageNum: 1, pageSize: 200 } })
    feeItems.value = (fi && fi.rows) || []
  } catch (e) { feeItems.value = [] }
}

function openGen() {
  Object.assign(g, { orgId: '', feeItemId: '', periodStart: '', periodEnd: '',
    billPeriod: '', dryRun: false })
  loadGenOptions()
  genVisible.value = true
}''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 出账选项加载')

# 批量催缴提示文案修正（selected.value 已改，消息不变）
# ================= Deposits =================
p = os.path.join(V, 'Deposits.vue')
patch(p, [
    ('''async function fillFromContract() {
  const cid = String(dp.contractId || '').trim()
  if (!/^\\d+$/.test(cid)) {
    if (cid) ElMessage.warning('合同ID应为数字，请从合同列表复制')
    return
  }
  dp.contractId = cid''',
     '''async function fillFromContract() {
  const cid = String(dp.contractId || '').trim()
  if (!cid) return
  if (!/^\\d+$/.test(cid)) {
    ElMessage.warning('合同ID为数字（可在合同列表复制）；也可改选人员，系统会自动带出合同')
    return
  }
  dp.contractId = cid''', '押金提示'),
    ('''<el-form-item label="人员ID"><PersonPicker v-model="dp.personId" width="240px" testid="person-picker" />''',
     '''<el-form-item label="人员ID"><PersonPicker v-model="dp.personId" width="240px"
                                testid="person-picker" @update:model-value="fillFromPerson" />''', '人员联动'),
])

s = io.open(p, encoding='utf-8').read()
if 'fillFromPerson' not in s.split('</template>')[0]:
    s = s.replace('''async function fillFromContract() {''', '''/** 选人员：带出其生效合同与应收押金 */
async function fillFromPerson(pid) {
  if (!pid) return
  try {
    const c = await req.get('/contracts/active-by-person/' + pid)
    if (c) {
      dp.contractId = c.id
      if (c.depositAmount != null) dp.depositAmount = c.depositAmount
      ElMessage.success('已带出合同 ' + (c.contractNo || c.id) + ' 与应收押金')
    } else {
      ElMessage.warning('该人员没有生效中的合同')
    }
  } catch (e) {
    ElMessage.warning('未找到该人员的合同')
  }
}

async function fillFromContract() {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 人员带出合同')
