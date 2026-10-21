# -*- coding: utf-8 -*-
"""前端：人员编辑 + 改状态下拉中文 + 保障档案编辑/枚举中文"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 枚举补齐 ----------
E = FE + r'\constants\enums.js'
e = io.open(E, encoding='utf-8').read()
NEW = {
    'LOW': '低保',
    'LOW_INCOME': '低收入',
    'MIDDLE_LOW': '中低收入',
    'BLACKLIST': '黑名单',
    'ACTIVE': '在保',
    'EXITED': '已退出',
    'PENDING_QUALIFY': '待认定',
    'QUALIFIED': '已认定',
    'SINGLE': '未婚',
    'MARRIED': '已婚',
    'DIVORCED': '离异',
    'WIDOWED': '丧偶',
    'URBAN': '城镇',
    'RURAL': '农村',
    'COUPLE': '夫妻',
    'SINGLE_PARENT': '单亲',
    'STAFF': '工作人员',
    'SYSTEM': '系统',
    'TENANT': '租户',
    'ALL': '全部',
    'DEPT': '本部门',
    'SELF': '仅本人',
}
add = [(k, v) for k, v in NEW.items()
       if not re.search(r"^\s*'?%s'?\s*:" % k, e, re.M)]
if add:
    block = '\n  // ---------- 人员/档案/权限（实测补充） ----------\n'
    for k, v in add:
        block += "  %s: '%s',\n" % (k, v)
    e = e.replace('  // ---------- 房源 / 空间 ----------',
                  block + '\n  // ---------- 房源 / 空间 ----------', 1)
    io.open(E, 'w', encoding='utf-8').write(e)
    print('  ✓ enums.js 补 %d 个' % len(add))

# ---------- 2) Persons.vue：编辑 + 改状态下拉 + 档案编辑 ----------
P = FE + r'\views\Persons.vue'
s = io.open(P, encoding='utf-8').read()

# 2.1 人员行内加「编辑」
if 'openEdit(row)' not in s:
    s = s.replace('''              <el-button link type="primary" @click="changeStatus(row)">改状态</el-button>''',
                  '''              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="primary" @click="changeStatus(row)">改状态</el-button>''', 1)

# 2.2 改状态：prompt → 中文下拉弹窗
s = s.replace('''async function changeStatus(row) {
  const { value } = await ElMessageBox.prompt('输入状态：NORMAL / FROZEN / CANCELLED',
    '变更人员状态', { inputValue: row.personStatus || 'NORMAL' })
  await req.post(`/persons/${row.id}/status`, { status: value })
  ElMessage.success('已更新'); loadPersons()
}''',
              '''const statusVisible = ref(false)
const statusTarget = ref(null)
const statusValue = ref('NORMAL')

const PERSON_STATUS = [
  { value: 'NORMAL', label: '正常' },
  { value: 'BLACKLIST', label: '黑名单' },
  { value: 'CANCELLED', label: '已注销' }
]

function changeStatus(row) {
  statusTarget.value = row
  statusValue.value = row.personStatus || 'NORMAL'
  statusVisible.value = true
}

async function doChangeStatus() {
  await req.post(`/persons/${statusTarget.value.id}/status`,
    { status: statusValue.value })
  ElMessage.success('状态已更新')
  statusVisible.value = false
  loadPersons()
}''', 1)

# 2.3 编辑人员（复用新增表单，改为 PUT）
s = s.replace('''function openPerson() {''',
              '''const editTarget = ref(null)

function openEdit(row) {
  editTarget.value = row
  // 回填：只填可改字段
  Object.assign(pf, {
    personName: row.personName || '',
    idCard: row.idCard || '',
    phone: row.phone || '',
    orgId: row.orgId ? Number(row.orgId) : null,
    householdType: row.householdType || 'URBAN',
    maritalStatus: row.maritalStatus || 'SINGLE',
    education: row.education || '',
    employer: row.employer || '',
    remark: row.remark || ''
  })
  personVisible.value = true
}

function openPerson() {
  editTarget.value = null''', 1)

# 2.4 提交：区分新增/编辑
s = s.replace('''async function doCreatePerson() {
  if (!pf.personName) { ElMessage.warning('请填写姓名'); return }
  saving.value = true
  try {
    await req.post('/persons', { ...pf })
    ElMessage.success('人员已创建')
    personVisible.value = false; loadPersons()
  } finally { saving.value = false }
}''',
              '''async function doCreatePerson() {
  if (!pf.personName) { ElMessage.warning('请填写姓名'); return }
  saving.value = true
  try {
    if (editTarget.value) {
      // 编辑：身份证号不改，其余按非空覆盖
      const { idCard, ...rest } = pf
      await req.put(`/persons/${editTarget.value.id}`, rest)
      ElMessage.success('人员信息已更新')
    } else {
      await req.post('/persons', { ...pf })
      ElMessage.success('人员已创建')
    }
    personVisible.value = false
    editTarget.value = null
    loadPersons()
  } finally { saving.value = false }
}''', 1)

# 2.5 弹窗标题随模式变化
s = s.replace('<el-dialog v-model="personVisible" title="新增人员" width="620px">',
              '<el-dialog v-model="personVisible"\n'
              '               :title="editTarget ? \'编辑人员\' : \'新增人员\'" width="620px">', 1)
# 编辑时证件号不可改
s = s.replace('''<el-col :span="12"><el-form-item label="身份证号">
            <el-input v-model="pf.idCard" placeholder="18 位，校验位需正确" /></el-form-item></el-col>''',
              '''<el-col :span="12"><el-form-item label="身份证号">
            <el-input v-model="pf.idCard" :disabled="!!editTarget"
                      placeholder="18 位，校验位需正确（编辑不可改）" /></el-form-item></el-col>''', 1)

# 2.6 保障档案：行内加「编辑」
if 'openProfileEdit(row)' not in s:
    s = s.replace('''              <el-button link type="primary" @click="openRecalc(row)">收入重算</el-button>''',
                  '''              <el-button link type="primary" @click="openProfileEdit(row)">编辑</el-button>
              <el-button link type="primary" @click="openRecalc(row)">收入重算</el-button>''', 1)

# 2.7 档案编辑：回填 + 复用 save（后端按 personId upsert）
s = s.replace('''function openProfileFor(row) {
  gf.personId = Number(row.id)
  profileVisible.value = true
}''',
              '''const profileEditMode = ref(false)

function openProfileFor(row) {
  profileEditMode.value = false
  gf.personId = Number(row.id)
  profileVisible.value = true
}

/** 编辑保障档案：回填已有值，保存时按 personId 覆盖 */
function openProfileEdit(row) {
  profileEditMode.value = true
  Object.assign(gf, {
    personId: Number(row.personId || row.id),
    securityType: row.securityType || 'PUBLIC',
    familySize: Number(row.familySize || 1),
    familyType: row.familyType || 'SINGLE',
    monthlyIncome: Number(row.monthlyIncome || 0),
    assetDeclare: Number(row.assetDeclare || 0),
    hasHouse: Number(row.hasHouse || 0),
    hasVehicle: Number(row.hasVehicle || 0)
  })
  profileVisible.value = true
}''', 1)

s = s.replace('<el-dialog v-model="profileVisible" title="保障档案建档" width="620px">',
              '<el-dialog v-model="profileVisible"\n'
              '               :title="profileEditMode ? \'编辑保障档案\' : \'保障档案建档\'" width="620px">', 1)

s = s.replace('''    await req.post('/guarantee-profiles', { ...gf })
    ElMessage.success('保障档案已建立')''',
              '''    await req.post('/guarantee-profiles', { ...gf })
    ElMessage.success(profileEditMode.value ? '保障档案已更新' : '保障档案已建立')''', 1)

# 2.8 收入档位 / 档案状态：中文
s = s.replace("{{ enumLabel('incomeLevel', row.incomeLevel) }}",
              "{{ row.incomeLevelLabel || enumLabel('incomeLevel', row.incomeLevel) }}")
s = s.replace("{{ enumLabel('profileStatus', row.profileStatus) }}",
              "{{ row.profileStatusLabel || enumLabel('profileStatus', row.profileStatus) }}")

# 2.9 状态弹窗模板
if 'statusVisible' not in s.split('</template>')[0]:
    s = s.replace('    <!-- 保障档案建档 ProfileCmd -->',
                  '''    <!-- 变更人员状态 -->
    <el-dialog v-model="statusVisible" title="变更人员状态" width="420px">
      <el-form label-width="90px">
        <el-form-item label="人员">
          <el-input :model-value="statusTarget?.personName" disabled />
        </el-form-item>
        <el-form-item label="新状态">
          <el-select v-model="statusValue" style="width:100%">
            <el-option v-for="o in PERSON_STATUS" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doChangeStatus">确认</el-button>
      </template>
    </el-dialog>

    <!-- 保障档案建档 ProfileCmd -->''', 1)

# 2.10 人员状态列也走中文
s = s.replace("{{ enumLabel('personStatus', row.personStatus) }}",
              "{{ row.personStatusLabel || enumLabel('personStatus', row.personStatus) }}")

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ Persons.vue：人员编辑 + 改状态中文下拉 + 档案编辑 + 枚举中文')
