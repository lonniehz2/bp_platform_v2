# -*- coding: utf-8 -*-
"""合同换房弹窗 + 换房表单自动带出/筛选。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')


def patch_file(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)


# ---------------- Contracts ----------------
p = os.path.join(V, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
# 改文案
s = s.replace('>换床</el-button>', '>换房</el-button>')
s = s.replace("ElMessage.success('已换床')", "ElMessage.success('已换房')")
s = s.replace("ElMessage.error(e?.response?.data?.message || '换床失败')",
              "ElMessage.error(e?.response?.data?.message || '换房失败')")
io.open(p, 'w', encoding='utf-8', newline='').write(s)

patch_file(p, [
    # 弹窗（原先缺失，点了没反应）
    ('''    <!-- 快捷签约 -->''', '''    <!-- 换房（原换床） -->
    <el-dialog v-model="swapVisible" title="合同换房" width="600px">
      <el-alert type="info" :closable="false" show-icon
                title="换房会把合同迁到目标房源所在空间，原房源释放，并留痕；请确认目标房源可租。" />
      <el-form :model="sw" label-width="100px" style="margin-top:12px">
        <el-form-item label="合同">
          <el-input :model-value="sw.contractNo" disabled />
        </el-form-item>
        <el-form-item label="承租人">
          <el-input :model-value="sw.personName" disabled />
        </el-form-item>
        <el-form-item label="原房源">
          <el-input :model-value="sw.oldHouseName" disabled />
        </el-form-item>
        <el-form-item label="原租期">
          <el-input :model-value="sw.leaseStart + ' ~ ' + sw.leaseEnd" disabled />
        </el-form-item>
        <el-form-item label="目标房源" required>
          <HouseSelect v-model="sw.targetHouseId" width="100%" testid="swap-house" />
        </el-form-item>
        <el-form-item label="换房原因">
          <el-input v-model="sw.reason" type="textarea" :rows="2"
                    placeholder="如 家庭人口增加 / 楼层不适" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="swapVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSwap">确认换房</el-button>
      </template>
    </el-dialog>

    <!-- 快捷签约 -->''', '换房弹窗'),
    ('''const sw = reactive({ contractId: null, contractNo: '', targetHouseId: '', reason: '' })''',
     '''const sw = reactive({ contractId: null, contractNo: '', targetHouseId: '', reason: '',
  personName: '', oldHouseName: '', leaseStart: '', leaseEnd: '' })''', 'sw 字段'),
    ('''function openSwap(row) {
  sw.contractId = row.id
  sw.contractNo = row.contractNo
  sw.targetHouseId = ''
  sw.reason = ''
  swapVisible.value = true
}''',
     '''function openSwap(row) {
  Object.assign(sw, {
    contractId: row.id,
    contractNo: row.contractNo,
    targetHouseId: '',
    reason: '',
    personName: row.lesseeName || row.personName || row.lesseePersonId,
    oldHouseName: row.houseIdName || row.houseName || row.houseId,
    leaseStart: row.leaseStart,
    leaseEnd: row.leaseEnd
  })
  swapVisible.value = true
}''', 'openSwap 预填'),
])

# ---------------- Exchanges ----------------
p = os.path.join(V, 'Exchanges.vue')
patch_file(p, [
    # 筛选：组织 + 关键字
    ('''      <el-input v-model="keyword" placeholder="关键字" clearable style="width:180px"''',
     '''      <OrgSelect v-model="orgId" width="200px" testid="ex-org" />
      <el-input v-model="keyword" placeholder="承租人姓名" clearable style="width:180px"''', '筛选控件'),
    # 新建弹窗：人员后自动带出合同/房源/家庭人口
    ('''            <el-input v-model="form.oldContractId" data-testid="f-oldContractId" /></el-form-item></el-col>''',
     '''            <el-input :model-value="auto.contractNo || form.oldContractId" disabled
                      data-testid="f-oldContractId" /></el-form-item></el-col>''', '原合同只读'),
    ('''            <el-input v-model="form.oldHouseId" data-testid="f-oldHouseId" /></el-form-item></el-col>''',
     '''            <el-input :model-value="auto.houseName || form.oldHouseId" disabled
                      data-testid="f-oldHouseId" /></el-form-item></el-col>''', '原房源只读'),
    ('''import PersonPicker from '@/components/PersonPicker.vue\'''',
     '''import PersonPicker from '@/components/PersonPicker.vue'
import OrgSelect from '@/components/OrgSelect.vue\'''', '导入'),
])

# Exchanges script logic（用 python 精确插入）
s = io.open(p, encoding='utf-8').read()
if 'auto.contractNo' not in s:
    # 找到 form 定义后插入 auto + watch
    import re
    m = re.search(r'const form = reactive\(\{.*?\}\)\n', s, re.S)
    if m:
        insert = m.group(0) + '''
const auto = reactive({ contractNo: '', houseName: '', orgName: '' })

/** 选择人员后自动带出原合同、原房源与原家庭人口 */
async function fillFromPerson(pid) {
  Object.assign(auto, { contractNo: '', houseName: '', orgName: '' })
  form.oldContractId = ''
  form.oldHouseId = ''
  if (!pid) return
  try {
    const ct = await req.get('/contracts/active-by-person/' + pid)
    if (ct) {
      form.oldContractId = ct.id
      form.oldHouseId = ct.houseId
      auto.contractNo = ct.contractNo
      auto.houseName = ct.houseIdName || ct.houseId
      auto.orgName = ct.orgIdName || ct.orgId
    }
    const gp = await req.get('/guarantee-profiles/person/' + pid).catch(() => null)
    if (gp && gp.familySize != null) form.familySizeBefore = gp.familySize
  } catch (e) { /* 保持手填 */ }
}
'''
        s = s.replace(m.group(0), insert, 1)
        print('  ✔ 自动带出函数')

    # watch personId（若已有 import 则补 watch）
    if 'watch(' not in s:
        s = s.replace("import { ref, reactive, onMounted } from 'vue'",
                      "import { ref, reactive, watch, onMounted } from 'vue'", 1)
    s = s.replace('''const createVisible = ref(false)''',
                  '''const createVisible = ref(false)
watch(() => form.personId, (pid) => fillFromPerson(pid))''', 1)
    # load 传 keyword/org
    if 'orgId: orgId.value' not in s:
        import re
        s = re.sub(r'(req\.get\(\'/exchanges\', \{\s*params: \{[^}]*?)\}\)',
                   lambda mm: mm.group(1) + ", keyword: keyword.value || undefined, "
                              "orgId: orgId.value || undefined })", s, count=1)
    if 'const orgId = ref' not in s:
        s = s.replace('const keyword = ref(\'\')', 'const keyword = ref(\'\')\nconst orgId = ref(\'\')', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('Exchanges 已更新')
