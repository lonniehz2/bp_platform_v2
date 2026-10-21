# -*- coding: utf-8 -*-
"""年审路由 + 补贴页表单 + 催缴页表单"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'
V = os.path.join(FE, 'views')

# ---------- 1) 年审路由 ----------
R = os.path.join(FE, 'router', 'index.js')
r = io.open(R, encoding='utf-8').read()
if "'/annual-reviews'" not in r:
    anchor = """  {
    path: '/contract-changes',
    name: 'contractchanges',
    component: () => import('@/views/ContractChanges.vue'),
    meta: { title: '合同变更', icon: 'EditPen' }
  }
]"""
    assert anchor in r, '路由锚点缺失'
    r = r.replace(anchor, anchor[:-2] + """,
  {
    path: '/annual-reviews',
    name: 'annualreviews',
    component: () => import('@/views/AnnualReviews.vue'),
    meta: { title: '年审复核', icon: 'Checked' }
  }
]""", 1)
    io.open(R, 'w', encoding='utf-8').write(r)
    print('  ✓ 年审路由已注册')

# ---------- 2) 补贴页（补批量发放/确认按钮） ----------
SP = os.path.join(V, 'Subsidies.vue')
s = io.open(SP, encoding='utf-8').read()
if 'batchVisible' not in s:
    # 在 toolbar 的 spacer 后插入按钮
    s = s.replace('''      <div class="spacer" />''',
                  '''      <div class="spacer" />
      <el-button type="success" @click="batchVisible = true">批量发放</el-button>''', 1)
    # 操作列加确认
    s = s.replace('''          <el-button link @click="detail = row; show = true">详情</el-button>''',
                  '''          <el-button link type="success" :disabled="row.recordStatus !== 'PENDING'"
                     @click="confirm(row)">确认发放</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>''', 1)
    # script 补状态与函数
    s = s.replace("const show = ref(false)",
                  '''const show = ref(false)
const batchVisible = ref(false)
const saving = ref(false)
const bf = reactive({ subsidyPeriod: '', orgId: 1, payMode: 'BANK', dryRun: false })''', 1)
    if 'import { ref, onMounted }' in s:
        s = s.replace('import { ref, onMounted }', 'import { ref, reactive, onMounted }', 1)
    s = s.replace("import { subsidyApi } from '@/api/modules'",
                  "import { subsidyApi } from '@/api/modules'\nimport { ElMessage } from 'element-plus'", 1)
    s = s.replace('onMounted(load)',
                  '''async function doBatch() {
  saving.value = true
  try {
    const r = await subsidyApi.batchGrant({ ...bf })
    ElMessage.success('发放完成：' + (r?.count ?? r ?? '已执行'))
    batchVisible.value = false; load()
  } finally { saving.value = false }
}
async function confirm(row) {
  await subsidyApi.confirm(row.id)
  ElMessage.success('已确认发放'); load()
}

onMounted(load)''', 1)
    # 弹窗
    s = s.replace('</template>', '''
    <el-dialog v-model="batchVisible" title="批量发放补贴" width="480px">
      <el-form :model="bf" label-width="110px">
        <el-form-item label="补贴周期"><el-input v-model="bf.subsidyPeriod"
          placeholder="2026-10" /></el-form-item>
        <el-form-item label="组织ID"><el-input v-model.number="bf.orgId" /></el-form-item>
        <el-form-item label="发放方式">
          <el-select v-model="bf.payMode" style="width:100%">
            <el-option label="银行代发" value="BANK" />
            <el-option label="抵扣租金" value="OFFSET" />
          </el-select></el-form-item>
        <el-form-item label="试算"><el-switch v-model="bf.dryRun" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doBatch">确认发放</el-button>
      </template>
    </el-dialog>
  </div>
</template>''', 1)
    # 去掉原来的结尾 </div></template>（避免重复）
    s = s.replace('  </div>\n</template>', '  </div>\n</template>', 1)
    io.open(SP, 'w', encoding='utf-8').write(s)
    print('  ✓ Subsidies.vue 补批量发放/确认')

# ---------- 3) 催缴页（补登记催缴/扫描） ----------
AR = os.path.join(V, 'Arrears.vue')
a = io.open(AR, encoding='utf-8').read()
if 'dunningVisible' not in a:
    a = a.replace('''      <div class="spacer" />''',
                  '''      <div class="spacer" />
      <el-button type="success" @click="dunningVisible = true">登记催缴</el-button>
      <el-button @click="scan">扫描生成催缴</el-button>''', 1)
    a = a.replace("const show = ref(false)",
                  '''const show = ref(false)
const dunningVisible = ref(false)
const saving = ref(false)
const df = reactive({ billId: null, personId: null, actionType: 'SMS',
  remark: '' })''', 1)
    if 'import { ref, onMounted }' in a:
        a = a.replace('import { ref, onMounted }', 'import { ref, reactive, onMounted }', 1)
    a = a.replace("import { financeApi } from '@/api/modules'",
                  "import { financeApi } from '@/api/modules'\nimport { ElMessage } from 'element-plus'\nimport req from '@/api/request'", 1)
    a = a.replace('onMounted(load)', '''async function doDunning() {
  if (!df.billId) { ElMessage.warning('请填写账单ID'); return }
  saving.value = true
  try {
    await req.post('/fin/dunnings', { ...df })
    ElMessage.success('催缴已登记')
    dunningVisible.value = false; load()
  } finally { saving.value = false }
}
async function scan() {
  const r = await financeApi.dunningScan()
  ElMessage.success('扫描完成：生成 ' + (r?.count ?? '若干') + ' 条催缴'); load()
}

onMounted(load)''', 1)
    a = a.replace('</template>', '''
    <el-dialog v-model="dunningVisible" title="登记催缴" width="460px">
      <el-form :model="df" label-width="110px">
        <el-form-item label="账单ID"><el-input v-model.number="df.billId" /></el-form-item>
        <el-form-item label="人员ID"><el-input v-model.number="df.personId" /></el-form-item>
        <el-form-item label="催缴方式">
          <el-select v-model="df.actionType" style="width:100%">
            <el-option label="短信" value="SMS" />
            <el-option label="电话" value="CALL" />
            <el-option label="上门" value="VISIT" />
            <el-option label="律师函" value="LETTER" />
          </el-select></el-form-item>
        <el-form-item label="备注"><el-input v-model="df.remark" type="textarea"
          :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dunningVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doDunning">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>''', 1)
    io.open(AR, 'w', encoding='utf-8').write(a)
    print('  ✓ Arrears.vue 补登记催缴/扫描')
