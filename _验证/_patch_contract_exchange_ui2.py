# -*- coding: utf-8 -*-
"""补：合同换房弹窗 + 换房页自动带出/筛选（第二轮）。"""
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
    return s


# ---------- Contracts：弹窗插入到模板末尾 ----------
p = os.path.join(V, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
if '合同换房' not in s:
    dialog = '''
    <!-- 换房 -->
    <el-dialog v-model="swapVisible" title="合同换房" width="600px">
      <el-alert type="info" :closable="false" show-icon
                title="换房会把合同迁到目标房源所在空间，原房源释放并留痕；请确认目标房源可租。" />
      <el-form :model="sw" label-width="100px" style="margin-top:12px">
        <el-form-item label="合同"><el-input :model-value="sw.contractNo" disabled /></el-form-item>
        <el-form-item label="承租人"><el-input :model-value="sw.personName" disabled /></el-form-item>
        <el-form-item label="原房源"><el-input :model-value="sw.oldHouseName" disabled /></el-form-item>
        <el-form-item label="原租期">
          <el-input :model-value="(sw.leaseStart || '') + ' ~ ' + (sw.leaseEnd || '')" disabled />
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
'''
    idx = s.rfind('</template>')
    s = s[:idx] + dialog + s[idx:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 合同换房弹窗')
else:
    print('  · 合同换房弹窗已存在')

# ---------- Exchanges ----------
p = os.path.join(V, 'Exchanges.vue')
patch_file(p, [
    ('''      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />''',
     '''      <OrgSelect v-model="orgId" width="200px" testid="ex-org" />
      <el-input v-model="keyword" placeholder="承租人姓名" clearable style="width:180px"
                @keyup.enter="reload" />''', '筛选控件'),
    ('''      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }''',
     '''      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined,
                orgId: orgId.value || undefined }''', 'load 参数'),
])

s = io.open(p, encoding='utf-8').read()
if 'const auto = reactive' not in s:
    s = s.replace('''  forceExchange: false
})
''', '''  forceExchange: false
})

const orgId = ref('')
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
''', 1)
    if 'watch(' not in s:
        s = s.replace("import { ref, reactive, onMounted } from 'vue'",
                      "import { ref, reactive, watch, onMounted } from 'vue'", 1)
    if 'watch(() => form.personId' not in s:
        s = s.replace('const createVisible = ref(false)',
                      'const createVisible = ref(false)\n'
                      'watch(() => form.personId, (pid) => fillFromPerson(pid))', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 自动带出逻辑')
