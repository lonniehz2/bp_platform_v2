# -*- coding: utf-8 -*-
"""合同变更详情、合同组织筛选、退租操作列、抄表录入能力。"""
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


# ================= 1. 合同变更详情 =================
p = os.path.join(V, 'ContractChanges.vue')
s = io.open(p, encoding='utf-8').read()
if 'openChange' not in s:
    s = s.replace('''          <el-button link @click="detail = row; show = true">详情</el-button>''',
                  '''          <el-button link @click="openChange(row)">详情</el-button>''', 1)
    # 弹窗
    s = s.replace('''    <el-pagination style="margin-top:12px"''', '''    <el-dialog v-model="changeVisible" title="合同变更详情" width="760px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="变更号">{{ current?.changeNo }}</el-descriptions-item>
        <el-descriptions-item label="合同">{{ current?.contractIdName || current?.contractId }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ current?.changeTypeLabel || current?.changeType }}</el-descriptions-item>
        <el-descriptions-item label="生效日">{{ current?.effectiveDate }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ current?.approveStatusLabel || current?.approveStatus }}</el-descriptions-item>
        <el-descriptions-item label="原因">{{ current?.reason || '—' }}</el-descriptions-item>
      </el-descriptions>
      <el-row :gutter="12" style="margin-top:10px">
        <el-col :span="12">
          <div class="card-title">变更前</div>
          <div class="kv">
            <div v-for="(v, k) in beforeObj" :key="k"><b>{{ k }}</b>：{{ v }}</div>
            <div v-if="!Object.keys(beforeObj).length" class="muted">—</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card-title">变更后</div>
          <div class="kv">
            <div v-for="(v, k) in afterObj" :key="k"><b>{{ k }}</b>：{{ v }}</div>
            <div v-if="!Object.keys(afterObj).length" class="muted">—</div>
          </div>
        </el-col>
      </el-row>
      <template #footer>
        <el-button @click="changeVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-pagination style="margin-top:12px"''', 1)
    if 'const changeVisible' not in s:
        s = s.replace('''const show = ref(false)''', '''const changeVisible = ref(false)
const current = ref(null)
const beforeObj = ref({})
const afterObj = ref({})

const FIELD_LABEL = {
  monthlyRent: '月租金', depositAmount: '押金', leaseStart: '开始日', leaseEnd: '结束日',
  lesseePersonId: '承租人', lesseeName: '承租人姓名', payCycle: '付款周期',
  payDay: '账单日', rentPrice: '租金单价', actualPay: '实付', subsidyAmount: '补贴',
  houseId: '房源', remark: '备注'
}

function pretty(raw) {
  if (raw == null || raw === '') return {}
  let obj = raw
  if (typeof raw === 'string') {
    try { obj = JSON.parse(raw) } catch (e) { return { 内容: raw } }
  }
  if (Array.isArray(obj)) return { 内容: obj.join('、') }
  if (typeof obj !== 'object') return { 内容: String(obj) }
  const out = {}
  Object.keys(obj).forEach((k) => { out[FIELD_LABEL[k] || k] = obj[k] })
  return out
}

function openChange(row) {
  current.value = row
  beforeObj.value = pretty(row.beforeJson ?? row.beforeContent ?? row.before)
  afterObj.value = pretty(row.afterJson ?? row.afterContent ?? row.after)
  changeVisible.value = true
}
const show = ref(false)''', 1)
    # 样式
    if '<style scoped>' in s:
        s = s.replace('<style scoped>', '''<style scoped>
.kv { border: 1px solid var(--el-border-color-lighter); border-radius: 4px; padding: 8px;
  font-size: 13px; line-height: 1.8; max-height: 260px; overflow: auto; }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 合同变更详情格式化')

# ================= 2. 合同组织筛选 =================
p = os.path.join(V, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
if 'orgFilterOptions' not in s:
    s = s.replace('''        <OrgSelect v-model="q.orgId" width="200px" testid="contract-org-filter"
                   placeholder="组织名称" @update:model-value="reload" />''',
                  '''        <el-select v-model="q.orgId" placeholder="组织名称" clearable filterable
                   style="width:200px" data-testid="contract-org-filter"
                   @change="reload">
          <el-option v-for="o in orgFilterOptions" :key="o.id"
                     :label="o.orgName" :value="String(o.id)" />
        </el-select>''', 1)
    if 'const orgFilterOptions' not in s:
        s = s.replace('''const q = reactive({''', '''const orgFilterOptions = ref([])
async function loadOrgFilter() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgFilterOptions.value = (d && d.rows) || []
  } catch (e) { orgFilterOptions.value = [] }
}

const q = reactive({''', 1)
        s = s.replace('onMounted(() => {', 'onMounted(() => { loadOrgFilter(); ', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 合同组织筛选')

# ================= 3. 退租操作列 =================
p = os.path.join(V, 'Terminations.vue')
s = io.open(p, encoding='utf-8').read()
if 'el-dropdown' not in s:
    s = s.replace('''      <el-table-column label="操作" width="560" fixed="right">''',
                  '''      <el-table-column label="操作" width="320" fixed="right">''', 1)
    s = s.replace('''          <el-button link type="primary" @click="doSubmit(row)">提交</el-button>
          <el-button link type="primary" @click="approve(row)">审批</el-button>
          <el-button link type="danger" @click="doReject(row)">驳回</el-button>
          <el-button link @click="doCancel(row)">取消</el-button>
          <el-button v-if="row.inspectStatus && row.inspectStatus !== 'PENDING'"''',
                  '''          <el-dropdown style="margin:0 8px">
            <el-button link type="primary">更多▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="doSubmit(row)">提交</el-dropdown-item>
                <el-dropdown-item @click="approve(row)">审批</el-dropdown-item>
                <el-dropdown-item @click="doReject(row)">驳回</el-dropdown-item>
                <el-dropdown-item @click="doCancel(row)">取消</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button v-if="row.inspectStatus && row.inspectStatus !== 'PENDING'"''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 退租操作列收窄')
