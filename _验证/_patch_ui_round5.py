# -*- coding: utf-8 -*-
"""账单批量出账/催缴/公摊名称；抄表筛选/批量出账；押金ID校验。"""
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
    ('''                       :label="f.feeItemName || f.feeItemCode || f.id" :value="String(f.id)" />''',
     '''                       :label="f.itemName || f.feeItemName || f.itemCode || f.id"
                       :value="String(f.id)" />''', '公摊项目名称'),
    ('''      <el-form :model="g" label-width="120px">
        <el-form-item label="组织ID"><el-input v-model="g.orgId" /></el-form-item>
        <el-form-item label="账期">
          <el-input v-model="g.billPeriod" placeholder="2026-10" /></el-form-item>
        <el-form-item label="试算（不落库）">
          <el-switch v-model="g.dryRun" /></el-form-item>
      </el-form>''',
     '''      <el-form :model="g" label-width="120px">
        <el-form-item label="组织">
          <el-select v-model="g.orgId" filterable clearable style="width:100%"
                     placeholder="按名称搜索组织">
            <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="收费项目" required>
          <el-select v-model="g.feeItemId" filterable style="width:100%"
                     placeholder="选择计费项目">
            <el-option v-for="f in feeItems" :key="f.id"
                       :label="f.itemName || f.feeItemName || f.id" :value="String(f.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="费用起始" required>
          <el-date-picker v-model="g.periodStart" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="费用截止" required>
          <el-date-picker v-model="g.periodEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="试算（不落库）">
          <el-switch v-model="g.dryRun" /></el-form-item>
      </el-form>''', '批量出账表单'),
    ('''async function dunning(row) {
  await financeApi.arrears({ billId: row.id })
  ElMessage.success('已发起催缴（可在催缴管理查看）')
}''',
     '''async function dunning(row) {
  await req.post('/fin/dunnings', {
    billId: row.id, personId: row.personId || undefined,
    dunningType: 'NOTICE', dunningContent: '账单 ' + (row.billNo || '') + ' 催缴'
  })
  ElMessage.success('已生成催缴记录（可在催缴管理查看）')
  load()
}

/** 批量催缴 */
async function batchDunning() {
  if (!selected.length) { ElMessage.warning('请先勾选账单'); return }
  let ok = 0
  for (const row of selected) {
    try {
      await req.post('/fin/dunnings', {
        billId: row.id, personId: row.personId || undefined,
        dunningType: 'NOTICE', dunningContent: '批量催缴'
      })
      ok++
    } catch (e) { /* 忽略单条失败 */ }
  }
  ElMessage.success('批量催缴完成：' + ok + ' 张')
  load()
}''', '催缴接口'),
])

# 选择列 + 批量催缴按钮
s = io.open(p, encoding='utf-8').read()
if 'batchDunning' in s and 'el-table-column type="selection"' not in s:
    s = s.replace('''      <el-table :data="rows"''', '''      <el-table :data="rows" @selection-change="(v) => (selected = v)"''', 1)
    s = s.replace('''      <el-table :data="rows"''', '''      <el-table :data="rows"''', 1)
    # 在第一列前插选择列
    s = s.replace('''    <el-table :data="rows" @selection-change="(v) => (selected = v)"''',
                  '''    <el-table :data="rows" @selection-change="(v) => (selected = v)"''', 1)
    idx = s.find('<el-table :data="rows"')
    if idx > 0:
        end = s.find('>', idx) + 1
        s = s[:end] + '\n      <el-table-column type="selection" width="42" />' + s[end:]
    s = s.replace('''        <el-button type="success" @click="genVisible = true">批量出账</el-button>''',
                  '''        <el-button type="success" @click="genVisible = true">批量出账</el-button>
        <el-button type="warning" plain @click="batchDunning">批量催缴</el-button>''', 1)
    if 'const selected = ref' not in s:
        s = s.replace('''const rows = ref([])''', '''const rows = ref([])
const selected = ref([])''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 批量催缴按钮/选择')

# g 初始字段 + doGenerate 参数
s = io.open(p, encoding='utf-8').read()
if 'periodStart' not in s.split('const g =')[1][:400]:
    s = s.replace('''const g = reactive({ orgId: '', billPeriod: '', dryRun: false })''',
                  '''const g = reactive({ orgId: '', feeItemId: '', periodStart: '', periodEnd: '',
  billPeriod: '', dryRun: false })''', 1)
s = s.replace('''    const r = await financeApi.generate({ ...g })''',
              '''    const r = await financeApi.generate({
      orgId: g.orgId || undefined, feeItemId: g.feeItemId,
      periodStart: g.periodStart, periodEnd: g.periodEnd,
      billPeriod: g.periodStart ? g.periodStart.slice(0, 7).replace('-', '') : g.billPeriod,
      dryRun: !!g.dryRun
    })''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('  ✔ 批量出账参数')

# ================= Meter =================
p = os.path.join(V, 'MeterReadings.vue')
patch(p, [
    ('''      <el-button type="primary" @click="load">查询</el-button>''',
     '''      <el-select v-model="query.orgId" placeholder="组织" clearable filterable
                 style="width:200px" @change="load">
        <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName"
                   :value="String(o.id)" />
      </el-select>
      <el-select v-model="query.billed" placeholder="出账状态" clearable
                 style="width:140px" @change="load">
        <el-option label="未出账" :value="false" />
        <el-option label="已出账" :value="true" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>''', '抄表筛选'),
    ('''        <el-button type="primary" plain @click="openBatch" data-testid="meter-batch">
        批量录入/导入
      </el-button>''',
     '''        <el-button type="primary" plain @click="openBatch" data-testid="meter-batch">
        批量录入/导入
      </el-button>
      <el-button type="warning" plain @click="batchBill">批量出账</el-button>''', '批量出账按钮'),
])

# 选择列 + 方法/状态
s = io.open(p, encoding='utf-8').read()
if 'batchBill' in s and 'meterSelected' not in s:
    s = s.replace('''    <el-table empty-text="暂无抄表记录，可人工录入或从 IoT 拉取" :data="rows"''',
                  '''    <el-table empty-text="暂无抄表记录，可人工录入或从 IoT 拉取" :data="rows"
              @selection-change="(v) => (meterSelected = v)"''', 1)
    idx = s.find('<el-table empty-text="暂无抄表记录')
    if idx > 0:
        end = s.find('>', idx) + 1
        s = s[:end] + '\n      <el-table-column type="selection" width="42" />' + s[end:]
    if 'const meterSelected' not in s:
        s = s.replace('''const rows = ref([])''', '''const rows = ref([])
const meterSelected = ref([])
const orgOptions = ref([])

async function loadOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = (d && d.rows) || []
  } catch (e) { orgOptions.value = [] }
}

async function batchBill() {
  const ids = meterSelected.value.filter((r) => !r.billId).map((r) => r.id)
  if (!ids.length) { ElMessage.warning('请勾选未出账的记录'); return }
  try {
    const r = await req.post('/fin/meter-readings/bill-batch', ids)
    ElMessage.success('出账完成：成功 ' + r.billed + '，失败 ' + r.failed)
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '批量出账失败')
  }
}''', 1)
        s = s.replace('''onMounted(''', '''onMounted(() => loadOrgs())
onMounted(''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 抄表批量出账/组织')

# load 参数带 orgId/billed
s = io.open(p, encoding='utf-8').read()
s = s.replace('''    if (query.feeItemId) params.feeItemId = query.feeItemId''',
              '''    if (query.feeItemId) params.feeItemId = query.feeItemId
    if (query.orgId) params.orgId = query.orgId
    if (query.billed !== '' && query.billed != null) params.billed = query.billed''', 1)
s = s.replace('''const query = reactive({ pageNum: 1, pageSize: 20, houseId: '', feeItemId: '' })''',
              '''const query = reactive({ pageNum: 1, pageSize: 20, houseId: '', feeItemId: '',
  orgId: '', billed: '' })''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('  ✔ 抄表查询参数')

# ================= Deposits：合同ID 类型保护 =================
p = os.path.join(V, 'Deposits.vue')
patch(p, [
    ('''async function fillFromContract() {
  if (!dp.contractId) return''',
     '''async function fillFromContract() {
  const cid = String(dp.contractId || '').trim()
  if (!/^\\d+$/.test(cid)) {
    if (cid) ElMessage.warning('合同ID应为数字，请从合同列表复制')
    return
  }
  dp.contractId = cid''', '押金合同ID校验'),
])
