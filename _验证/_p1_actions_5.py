# -*- coding: utf-8 -*-
"""P1 接线（第四批）：合同变更从合同发起、资金流水核验。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')

# ---------- 合同变更：从合同发起变更 ----------
p = os.path.join(V, 'ContractChanges.vue')
s = io.open(p, encoding='utf-8').read()
if 'doCreateChange' not in s:
    # 工具栏加按钮
    s = s.replace("""<el-button type="primary" @click="load">查询</el-button>""",
                  """<el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openCreate">发起变更</el-button>""", 1)
    s = s.replace("""<el-button @click="load">查询</el-button>""",
                  """<el-button @click="load">查询</el-button>
        <el-button type="success" @click="openCreate">发起变更</el-button>""", 1)
    # 弹窗 + 逻辑
    s = s.replace('</script>', """const createVisible = ref(false)
const cf = reactive({ contractId: null, changeType: 'RENT_ADJUST',
  newMonthlyRent: null, newLeaseEnd: '', changeReason: '' })

function openCreate() {
  Object.assign(cf, { contractId: null, changeType: 'RENT_ADJUST',
    newMonthlyRent: null, newLeaseEnd: '', changeReason: '' })
  createVisible.value = true
}

/** 从合同发起变更（统一走 /contracts/{id}/changes） */
async function doCreateChange() {
  if (!cf.contractId) { ElMessage.warning('请填写合同ID'); return }
  if (cf.changeType === 'RENT_ADJUST' && !cf.newMonthlyRent) {
    ElMessage.warning('调租请填写新租金'); return
  }
  await req.post(`/contracts/${cf.contractId}/changes`, {
    changeType: cf.changeType,
    changeReason: cf.changeReason,
    newMonthlyRent: cf.newMonthlyRent || null,
    newLeaseEnd: cf.newLeaseEnd || null
  })
  ElMessage.success('变更单已创建，待审批')
  createVisible.value = false
  load()
}
</script>""", 1)
    # 模板补弹窗
    idx = s.rfind('</el-drawer>')
    if idx > 0:
        dlg = """
    <el-dialog v-model="createVisible" title="从合同发起变更" width="520px">
      <el-form :model="cf" label-width="120px">
        <el-form-item label="合同ID" required>
          <el-input v-model.number="cf.contractId" />
        </el-form-item>
        <el-form-item label="变更类型" required>
          <el-select v-model="cf.changeType" style="width:100%">
            <el-option label="调租" value="RENT_ADJUST" />
            <el-option label="续租" value="RENEW" />
            <el-option label="租期调整" value="PERIOD" />
            <el-option label="变更承租人" value="LESSEE" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="cf.changeType === 'RENT_ADJUST' || cf.changeType === 'RENEW'"
                      label="新月租金">
          <el-input v-model.number="cf.newMonthlyRent" />
        </el-form-item>
        <el-form-item v-if="cf.changeType === 'PERIOD' || cf.changeType === 'RENEW'"
                      label="新止租日">
          <el-date-picker v-model="cf.newLeaseEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="变更原因">
          <el-input v-model="cf.changeReason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="doCreateChange">创建</el-button>
      </template>
    </el-dialog>
"""
        s = s[:idx + len('</el-drawer>')] + dlg + s[idx + len('</el-drawer>'):]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('合同变更页已加「发起变更」')
else:
    print('合同变更页已存在')

# 导入检查
p = os.path.join(V, 'ContractChanges.vue')
s = io.open(p, encoding='utf-8').read()
if "'@/api/request'" not in s:
    s = s.replace("import { ref, reactive, onMounted } from 'vue'",
                  "import { ref, reactive, onMounted } from 'vue'\nimport req from '@/api/request'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('合同变更导入 req')

# ---------- 资金流水：核验 ----------
p = os.path.join(V, 'Cashflow.vue')
if not os.path.exists(p):
    p = os.path.join(V, 'CashFlow.vue')
s = io.open(p, encoding='utf-8').read()
if 'doVerify' not in s:
    s = s.replace("""          <el-button link @click="detail = row; show = true">详情</el-button>""",
                  """          <el-button link type="success" :disabled="row.verifyStatus === 'VERIFIED'"
                     @click="doVerify(row)">核验</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>""", 1)
    s = s.replace('<el-table-column label="操作" width="120" fixed="right">',
                  '<el-table-column label="操作" width="180" fixed="right">', 1)
    s = s.replace('</script>', """/** 流水核验：与银行/支付渠道对账后标记 */
async function doVerify(row) {
  await ElMessageBox.confirm('确认该笔流水已与渠道核对一致？', '核验流水',
    { type: 'warning' })
  await req.post(`/fin/cash-flows/${row.id}/verify`)
  ElMessage.success('已核验')
  load()
}
</script>""", 1)
    if "'@/api/request'" not in s:
        s = s.replace("import { detail } from", "import { detail } from", 1)
        # 插入到首个 import 之后
        idx = s.find('import ')
        s = s[:idx] + "import req from '@/api/request'\n" + s[idx:]
    if 'ElMessageBox' not in s:
        s = s.replace("import { ElMessage } from 'element-plus'",
                      "import { ElMessage, ElMessageBox } from 'element-plus'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('资金流水页已加「核验」')
else:
    print('资金流水页已存在')
