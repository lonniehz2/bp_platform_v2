# -*- coding: utf-8 -*-
"""前端：合同页「快捷签约」入口 + 公示页中签名单。

1) Contracts.vue：工具栏「快捷签约」→ 选人 + 选空置房源 + 租期金额 → POST /contracts/quick-sign
2) Publicity 页：新建公示可选关联批次；详情弹窗加载 /publicities/{id}/winners 展示名单
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---------------- 1) Contracts.vue ----------------
p = os.path.join(V, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()

if 'quickSignVisible' not in s:
    # 工具栏按钮
    m = re.search(r'(<el-button type="success"[^>]*@click="openCreate"[^>]*>[^<]*新建合同[^<]*</el-button>)', s)
    if m:
        s = s[:m.end()] + ('\n          <el-button type="primary" plain @click="openQuickSign"\n'
                           '                     data-testid="quick-sign">快捷签约</el-button>') + s[m.end():]

    dialog = '''
    <!-- 快捷签约：存量人员 + 空置房源直接签约 -->
    <el-dialog v-model="quickSignVisible" title="快捷签约（线下受理）" width="640px">
      <el-alert type="info" :closable="false" show-icon
                title="用于存量人员/房源直接签约：系统会自动补一张「线下受理」申请单，保证可追溯" />
      <el-form :model="qf" label-width="100px" style="margin-top:12px">
        <el-form-item label="承租人" required>
          <PersonPicker v-model="qf.personId" />
        </el-form-item>
        <el-form-item label="房源" required>
          <el-select v-model="qf.houseId" filterable remote :remote-method="searchVacantHouse"
                     :loading="houseLoading" style="width:100%" placeholder="输入房号搜索空置房源">
            <el-option v-for="h in vacantHouses" :key="h.id"
                       :label="`${h.houseName}（${h.orgIdName || ''}）`" :value="String(h.id)" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="起租日" required>
            <el-date-picker v-model="qf.leaseStart" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="止租日" required>
            <el-date-picker v-model="qf.leaseEnd" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="月租" required>
            <el-input v-model="qf.monthlyRent" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="押金">
            <el-input v-model="qf.depositAmount" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="保障类型">
            <el-select v-model="qf.securityType" style="width:100%">
              <el-option label="公租房" value="PUBLIC" />
              <el-option label="经适房" value="AFFORDABLE" />
              <el-option label="人才房" value="TALENT" />
              <el-option label="廉租房" value="LOW_RENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="qf.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="quickSignVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doQuickSign">生成合同</el-button>
      </template>
    </el-dialog>
'''
    idx = s.rfind('</template>')
    s = s[:idx] + dialog + s[idx:]

    script = '''
/** 快捷签约（存量人员+空置房源直接出合同） */
const quickSignVisible = ref(false)
const vacantHouses = ref([])
const houseLoading = ref(false)
const qf = reactive({ personId: '', houseId: '', leaseStart: '', leaseEnd: '',
  monthlyRent: 0, depositAmount: 0, securityType: 'PUBLIC', remark: '存量直接签约' })

function openQuickSign() {
  Object.assign(qf, { personId: '', houseId: '', leaseStart: '', leaseEnd: '',
    monthlyRent: 0, depositAmount: 0, securityType: 'PUBLIC', remark: '存量直接签约' })
  vacantHouses.value = []
  quickSignVisible.value = true
  searchVacantHouse('')
}

async function searchVacantHouse(kw) {
  houseLoading.value = true
  try {
    const d = await req.get('/houses', { params: { pageNum: 1, pageSize: 20,
      status: 'VACANT', keyword: kw || undefined } })
    vacantHouses.value = (d && d.rows) || []
  } finally { houseLoading.value = false }
}

async function doQuickSign() {
  if (!qf.personId) { ElMessage.warning('请选择承租人'); return }
  if (!qf.houseId) { ElMessage.warning('请选择房源'); return }
  if (!qf.leaseStart || !qf.leaseEnd) { ElMessage.warning('请填写起止租期'); return }
  if (!qf.monthlyRent) { ElMessage.warning('请填写月租'); return }
  saving.value = true
  try {
    const c = await req.post('/contracts/quick-sign', { ...qf })
    ElMessage.success(`已生成合同 ${c?.contractNo || ''}（草稿）`)
    quickSignVisible.value = false
    load()
  } finally { saving.value = false }
}
'''
    anchor = 'onMounted(load)'
    if anchor in s:
        s = s.replace(anchor, script + '\n' + anchor, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('Contracts.vue：快捷签约入口已加')
else:
    print('Contracts.vue：已存在')
