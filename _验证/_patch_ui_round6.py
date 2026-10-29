# -*- coding: utf-8 -*-
"""欠费处置组织/自动带出；账单收费项目列；批量子房源按组织。"""
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


# ---------- Arrears ----------
p = os.path.join(V, 'Arrears.vue')
patch(p, [
    ('''        <el-form-item label="合同ID" required>
          <el-input v-model.number="nf.contractId" />
        </el-form-item>
        <el-form-item label="人员ID" required>
          <el-input v-model.number="nf.personId" />
        </el-form-item>''',
     '''        <el-form-item label="组织">
          <el-select v-model="nf.orgId" filterable clearable style="width:100%"
                     placeholder="按名称搜索组织">
            <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="合同" required>
          <ContractSelect v-model="nf.contractId" width="100%"
                          @update:model-value="() => fillFromArrears('contract')" />
        </el-form-item>
        <el-form-item label="人员" required>
          <PersonPicker v-model="nf.personId" width="100%"
                        @update:model-value="() => fillFromArrears('person')" />
        </el-form-item>''', '处置表单'),
])

s = io.open(p, encoding='utf-8').read()
if 'fillFromArrears' not in s:
    s = s.replace('''function openAction() {''', '''const orgOptions = ref([])
async function loadOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = (d && d.rows) || []
  } catch (e) { orgOptions.value = [] }
}

/** 输入合同或人员后，自动带出欠费金额、逾期天数与另一方 */
async function fillFromArrears(source) {
  const params = {}
  if (source === 'contract') {
    params.contractId = nf.contractId || undefined
  } else {
    params.personId = nf.personId || undefined
  }
  if (!params.contractId && !params.personId) return
  try {
    const d = await req.get('/fin/arrears/summary', { params })
    if (!d) return
    if (source === 'contract') {
      if (d.person_id) nf.personId = d.person_id
    } else if (d.contract_id) {
      nf.contractId = d.contract_id
    }
    if (d.org_id) nf.orgId = String(d.org_id)
    nf.arrearsAmount = d.amount != null ? Number(d.amount) : nf.arrearsAmount
    nf.overdueDays = d.days != null ? Number(d.days) : nf.overdueDays
  } catch (e) { /* 保留手填 */ }
}

function openAction() {
  loadOrgs()''', 1)
    s = s.replace('''  Object.assign(nf, { contractId: undefined, personId: undefined,
    arrearsAmount: undefined, overdueDays: undefined, actionType: 'NOTIFY',''',
                  '''  Object.assign(nf, { orgId: '', contractId: undefined, personId: undefined,
    arrearsAmount: undefined, overdueDays: undefined, actionType: 'NOTIFY',''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 处置自动带出')

# nf 定义加 orgId
s = io.open(p, encoding='utf-8').read()
s = s.replace('''const nf = reactive({ contractId: undefined''',
              '''const nf = reactive({ orgId: '', contractId: undefined''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)

# ---------- Bills 收费项目列 ----------
p = os.path.join(V, 'Bills.vue')
patch(p, [
    ('''        <el-table-column prop="billPeriod" label="账期" width="95" />''',
     '''        <el-table-column prop="billPeriod" label="账期" width="95" />
        <el-table-column label="收费项目" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.feeItemIdName || row.feeItemName || row.feeItemId || '—' }}
          </template>
        </el-table-column>''', '收费项目列'),
])

# ---------- Meter 批量：房源按组织 ----------
p = os.path.join(V, 'MeterReadings.vue')
patch(p, [
    ('''            <HouseSelect :model-value="row.houseId" width="100%"
                         @update:model-value="(v) => onRowHouse(row, v)" />''',
     '''            <HouseSelect :model-value="row.houseId" :org-id="row.orgId" width="100%"
                         @update:model-value="(v) => onRowHouse(row, v)" />''', '批量子房源'),
])
