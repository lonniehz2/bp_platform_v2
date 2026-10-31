# -*- coding: utf-8 -*-
import io

# 1) 批量出账：规则方式与规则选择
p = r'..\frontend\src\views\Bills.vue'
s = io.open(p, encoding='utf-8').read()

if 'g.ruleMode' not in s:
    s = s.replace('''            <el-form-item label="收费项目" required>
              <el-select v-model="g.feeItemId" filterable style="width:100%"
                         placeholder="选择计费项目">
                <el-option v-for="f in feeItems" :key="f.id"
                           :label="f.itemName || f.feeItemName || f.id" :value="String(f.id)" />
              </el-select>
            </el-form-item>''', '''            <el-form-item label="收费项目" required>
              <el-select v-model="g.feeItemId" filterable style="width:100%"
                         placeholder="选择计费项目" @change="loadGenRules">
                <el-option v-for="f in feeItems" :key="f.id"
                           :label="f.itemName || f.feeItemName || f.id" :value="String(f.id)" />
              </el-select>
            </el-form-item>
            <el-form-item label="计费规则">
              <el-radio-group v-model="g.ruleMode">
                <el-radio-button label="AUTO">自动匹配</el-radio-button>
                <el-radio-button label="MANUAL">指定规则</el-radio-button>
                <el-radio-button label="NONE">不使用</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="g.ruleMode === 'MANUAL'" label="指定规则" required>
              <el-select v-model="g.ruleId" filterable style="width:100%"
                         placeholder="选择已审批规则">
                <el-option v-for="r in genRules" :key="r.id"
                           :label="r.ruleName + '（' + r.ruleType + '）'" :value="String(r.id)" />
              </el-select>
            </el-form-item>''', 1)

    s = s.replace('''const g = reactive({ orgId: null, billPeriod: '', dryRun: true })''',
                  '''const g = reactive({ orgId: null, billPeriod: '', dryRun: true,
  ruleMode: 'AUTO', ruleId: '', feeItemId: '', periodStart: '', periodEnd: '' })
const genRules = ref([])

async function loadGenRules() {
  genRules.value = []
  if (!g.feeItemId) return
  try {
    const list = await req.get('/fin/billing-rules', { params: { feeItemId: g.feeItemId } })
    genRules.value = (list || []).filter((r) =>
      r.approveStatus === 'APPROVED' && r.status === 'ENABLED')
  } catch (e) { genRules.value = [] }
}''', 1)

    s = s.replace('''  Object.assign(g, { orgId: '', feeItemId: '', periodStart: '', periodEnd: '',
    billPeriod: '', dryRun: false })
  loadGenOptions()''', '''  Object.assign(g, { orgId: '', feeItemId: '', periodStart: '', periodEnd: '',
    billPeriod: '', dryRun: false, ruleMode: 'AUTO', ruleId: '' })
  genRules.value = []
  loadGenOptions()''', 1)

    s = s.replace('''  if (!g.periodStart || !g.periodEnd) { ElMessage.warning('请选择费用起止日'); return }
  if (g.periodEnd <= g.periodStart) { ElMessage.warning('费用截止日必须晚于起始日'); return }''',
                  '''  if (!g.periodStart || !g.periodEnd) { ElMessage.warning('请选择费用起止日'); return }
  if (g.periodEnd <= g.periodStart) { ElMessage.warning('费用截止日必须晚于起始日'); return }
  if (g.ruleMode === 'MANUAL' && !g.ruleId) {
    ElMessage.warning('请选择指定的计费规则'); return
  }''', 1)

    s = s.replace('''      const r = await financeApi.generate({
        orgId: g.orgId || undefined, feeItemId: g.feeItemId,
        periodStart: g.periodStart, periodEnd: g.periodEnd,
        billPeriod: g.periodStart.slice(0, 7).replace('-', ''),
        dryRun: !!g.dryRun
      })''', '''      const r = await financeApi.generate({
        orgId: g.orgId || undefined, feeItemId: g.feeItemId,
        periodStart: g.periodStart, periodEnd: g.periodEnd,
        billPeriod: g.periodStart.slice(0, 7),
        ruleMode: g.ruleMode,
        ruleId: g.ruleMode === 'MANUAL' ? g.ruleId : undefined,
        dryRun: !!g.dryRun
      })''', 1)

    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('bills rule UI patched')

# 2) 合同详情展示计费人口/床位
p = r'..\frontend\src\views\Contracts.vue'
s = io.open(p, encoding='utf-8').read()
if 'billingPersonCount' not in s:
    s = s.replace('''        <el-descriptions-item label="月租">{{ detail.monthlyRent }}</el-descriptions-item>''',
                  '''        <el-descriptions-item label="月租">{{ detail.monthlyRent }}</el-descriptions-item>
        <el-descriptions-item label="计费人口">{{ detail.billingPersonCount || 1 }}</el-descriptions-item>
        <el-descriptions-item label="计费床位">{{ detail.billingBedCount || 1 }}</el-descriptions-item>''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('contract detail quantity')
