<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">保障对象</h3>
      <el-tag size="small" type="info">建档 → 实名核验 → 保障档案 → 资格判定</el-tag>
      <div class="spacer" />
      <el-select v-model="orgId" filterable clearable placeholder="全部组织"
                 style="width:220px" data-testid="person-org-filter">
        <el-option label="全部组织" :value="null" />
        <el-option v-for="o in orgOptions" :key="o.id"
                   :label="orgOptionLabel(o)" :value="Number(o.id)" />
      </el-select>
      <el-button type="primary" @click="reloadAll">查询</el-button>
      <el-button @click="resetAllQuery">清空</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon
              title="顺序约束：申请前必须通过实名核验（D32）；审核通过前必须有保障档案（D33）"
              style="margin-bottom:12px" />

    <el-tabs v-model="tab" @tab-change="onTab">
      <!-- ============ 人员档案 ============ -->
      <el-tab-pane label="人员档案" name="person">
        <div class="toolbar">
          <el-input v-model="keyword" placeholder="姓名 / 证件号" clearable
                    style="width:190px" @keyup.enter="loadPersons" />
          <el-button @click="loadPersons">查询</el-button>
          <el-button @click="resetPersonQuery">清空</el-button>
          <el-button @click="queryByIdCard">按证件号精确查</el-button>
          <div class="spacer" />
          <el-button type="success" @click="openPerson">新增人员</el-button>
        </div>
        <el-table :data="persons" v-loading="loading" border size="small">
          <el-table-column prop="personName" label="姓名" width="110" />
          <el-table-column label="所属组织" min-width="160">
            <template #default="{ row }">{{ orgNameOf(row.orgId) }}</template>
          </el-table-column>
          <el-table-column prop="idCardMask" label="证件号" width="190">
            <template #default="{ row }">{{ row.idCard || row.idCardMask || '-' }}</template>
          </el-table-column>
          <el-table-column prop="phoneMask" label="手机号" width="140" />
          <el-table-column label="户籍" width="90">
            <template #default="{ row }">{{ enumLabel('householdType', row.householdType) }}</template>
          </el-table-column>
          <el-table-column label="婚姻" width="90">
            <template #default="{ row }">{{ enumLabel('maritalStatus', row.maritalStatus) }}</template>
          </el-table-column>
          <el-table-column prop="personStatus" label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.personStatus === 'NORMAL' ? 'success'
                : (row.personStatus === 'FROZEN' ? 'warning' : 'info')">
                {{ row.personStatusLabel || enumLabel('personStatus', row.personStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="330" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="primary" @click="changeStatus(row)">改状态</el-button>
              <el-button link @click="openProfileFor(row)">保障档案</el-button>
              <el-button link @click="openVerifyFor(row)">实名核验</el-button>
              <el-button link type="danger" @click="removePerson(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                       :total="pTotal" :page-size="pQuery.pageSize"
                       :current-page="pQuery.pageNum"
                       @current-change="(p) => { pQuery.pageNum = p; loadPersons() }" />
      </el-tab-pane>

      <!-- ============ 保障档案 ============ -->
      <el-tab-pane label="保障档案" name="profile">
        <div class="toolbar">
          <el-button type="success" @click="profileVisible = true">建档</el-button>
          <el-button @click="loadExpiring">临近到期</el-button>
          <el-input v-model.number="expiringDays" placeholder="天数" style="width:90px"
                    data-testid="expiring-days" @keyup.enter="loadExpiring" />
          <div class="spacer" />
          <el-input v-model="gQuery.keyword" placeholder="姓名 / 手机 / 证件号" clearable
                    style="width:220px" data-testid="profile-keyword"
                    @keyup.enter="loadProfiles" />
          <el-button @click="loadProfileByPerson">查看</el-button>
        </div>
        <el-table :data="profiles" v-loading="loading" border size="small">
          <el-table-column label="保障对象" width="230">
            <template #default="{ row }">
              <div>{{ row.personName || row.personId }}</div>
              <div class="muted" style="font-size:12px">
                {{ row.phoneMask || '-' }}　{{ row.idCardMask || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="保障类型" width="110">
            <template #default="{ row }">
              {{ row.securityTypeLabel || enumLabel('securityType', row.securityType) }}
            </template>
          </el-table-column>
          <el-table-column prop="familySize" label="家庭人口" width="100" />
          <el-table-column prop="monthlyIncome" label="月收入" width="110">
            <template #default="{ row }">{{ money(row.monthlyIncome) }}</template>
          </el-table-column>
          <el-table-column label="收入档位" width="130">
            <template #default="{ row }">
              <el-tag v-if="row.incomeLevelLabel || row.incomeLevel" size="small">
                {{ row.incomeLevelLabel || enumLabel('incomeLevel', row.incomeLevel) }}
              </el-tag>
              <span v-else class="muted">未评定</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">{{ row.profileStatusLabel || enumLabel('profileStatus', row.profileStatus) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openProfileEdit(row)">编辑</el-button>
              <el-button link type="primary" @click="openRecalc(row)">收入重算</el-button>
              <el-button link type="success" @click="qualify(row)">资格判定</el-button>
              <el-button link type="danger" @click="exitProfile(row)">退出保障</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                       :total="gTotal" :page-size="gQuery.pageSize"
                       :current-page="gQuery.pageNum"
                       @current-change="(p) => { gQuery.pageNum = p; loadProfiles() }" />
      </el-tab-pane>

      <!-- ============ 实名核验 ============ -->
      <el-tab-pane label="实名核验" name="verify">
        <div class="toolbar">
          <el-button type="success" @click="verifyVisible = true">发起核验</el-button>
          <el-button @click="loadFailStats">失败统计</el-button>
          <div class="spacer" />
          <el-input v-model="vQuery.keyword" placeholder="姓名 / 手机 / 证件号" clearable
                    style="width:220px" data-testid="verify-keyword"
                    @keyup.enter="loadVerifies" />
          <el-button @click="loadConclusion">查结论</el-button>
        </div>
        <el-table :data="verifies" v-loading="loading" border size="small">
          <el-table-column label="核验对象" width="240">
            <template #default="{ row }">
              <div>{{ row.personName || row.personId }}</div>
              <div class="muted" style="font-size:12px">
                {{ row.phoneMask || '-' }}　{{ row.idCardMask || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column label="核验方式" width="130">
            <template #default="{ row }">
              {{ enumLabel('verifyType', row.verifyType) || row.verifyType }}
            </template>
          </el-table-column>
          <el-table-column label="结果" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="Number(row.verifyPass) === 1 ? 'success' : 'danger'">
                {{ Number(row.verifyPass) === 1 ? '通过' : '未通过' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="faceScore" label="人脸分" width="100" />
          <el-table-column prop="responseCode" label="返回码" width="100" />
          <el-table-column prop="verifyTime" label="核验时间" width="170" />
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button v-if="Number(row.verifyPass) !== 1" link type="primary"
                         @click="openVerifyFor(row)">实名核验</el-button>
              <span v-else class="muted">已通过</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                       :total="vTotal" :page-size="vQuery.pageSize"
                       :current-page="vQuery.pageNum"
                       @current-change="(p) => { vQuery.pageNum = p; loadVerifies() }" />
      </el-tab-pane>
    </el-tabs>

    <!-- 新增人员 PersonCreateCmd -->
    <el-dialog v-model="personVisible"
               :title="editTarget ? '编辑人员' : '新增人员'" width="620px">
      <el-form :model="pf" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="姓名" required>
            <el-input v-model="pf.personName" data-testid="person-name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="身份证号">
            <el-input v-model="pf.idCard" :disabled="!!editTarget"
                      placeholder="18 位，校验位需正确（编辑不可改）" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="手机号">
            <el-input v-model="pf.phone" data-testid="person-phone"
                      placeholder="编辑时留空表示不修改" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="所属组织">
            <el-select v-model="pf.orgId" filterable clearable style="width:100%"
                       placeholder="选择组织（可空）" data-testid="person-org">
              <el-option v-for="o in orgOptions" :key="o.id"
                         :label="o.orgName" :value="Number(o.id)" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="户籍类型">
            <el-select v-model="pf.householdType" style="width:100%">
              <el-option label="城镇" value="URBAN" />
              <el-option label="农村" value="RURAL" />
              <el-option label="其他" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="婚姻状况">
            <el-select v-model="pf.maritalStatus" style="width:100%">
              <el-option label="未婚" value="SINGLE" />
              <el-option label="已婚" value="MARRIED" />
              <el-option label="离异" value="DIVORCED" />
              <el-option label="丧偶" value="WIDOWED" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="学历">
            <el-input v-model="pf.education" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="工作单位">
            <el-input v-model="pf.employer" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="pf.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="personVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreatePerson">保存</el-button>
      </template>
    </el-dialog>

    <!-- 变更人员状态 -->
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

    <!-- 保障档案建档 ProfileCmd -->
    <el-dialog v-model="profileVisible"
               :title="profileEditMode ? '编辑保障档案' : '保障档案建档'" width="620px">
      <el-form :model="gf" label-width="130px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="人员ID" required>
            <el-input v-model="gf.personId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="保障类型">
            <el-select v-model="gf.securityType" style="width:100%">
              <el-option label="公租房" value="PUBLIC" />
              <el-option label="保租房" value="AFFORDABLE" />
              <el-option label="人才房" value="TALENT" />
              <el-option label="廉租房" value="LOW_RENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="家庭人口">
            <el-input-number v-model="gf.familySize" :min="1" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="家庭类型">
            <el-select v-model="gf.familyType" style="width:100%">
              <el-option label="单身" value="SINGLE" />
              <el-option label="夫妻" value="COUPLE" />
              <el-option label="单亲" value="SINGLE_PARENT" />
              <el-option label="其他" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="家庭月收入">
            <el-input-number v-model="gf.monthlyIncome" :min="0" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="资产申报(万元)">
            <el-input-number v-model="gf.assetDeclare" :min="0" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="名下有房">
            <el-switch v-model="gf.hasHouse" :active-value="1" :inactive-value="0" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="名下有车">
            <el-switch v-model="gf.hasVehicle" :active-value="1" :inactive-value="0" />
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="建档后会自动计算人均收入与收入档位（LOW / LOW_INCOME / MIDDLE_LOW / NORMAL）" />
      <template #footer>
        <el-button @click="profileVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateProfile">保存</el-button>
      </template>
    </el-dialog>

    <!-- 收入重算 IncomeCmd -->
    <el-dialog v-model="recalcVisible" title="收入档位重算" width="480px">
      <el-form :model="ic" label-width="140px">
        <el-form-item label="低保线">
          <el-input-number v-model="ic.lowLine" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="低收入线">
          <el-input-number v-model="ic.lowIncomeLine" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="中低收入线">
          <el-input-number v-model="ic.middleLowLine" :precision="2" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recalcVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRecalc">重算</el-button>
      </template>
    </el-dialog>

    <!-- 退出保障 ExitCmd -->
    <el-dialog v-model="exitVisible" title="退出保障" width="480px">
      <el-form :model="ex" label-width="120px">
        <el-form-item label="退出日期">
          <el-date-picker v-model="ex.exitDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" /></el-form-item>
        <el-form-item label="退出原因">
          <el-input v-model="ex.exitReason" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exitVisible = false">取消</el-button>
        <el-button type="danger" :loading="saving" @click="doExit">确认退出</el-button>
      </template>
    </el-dialog>

    <!-- 发起实名核验 VerifyCmd -->
    <el-dialog v-model="verifyVisible" title="发起实名核验" width="560px">
      <el-form :model="vf" label-width="130px">
        <el-form-item label="人员ID" required>
          <el-input v-model="vf.personId" /></el-form-item>
        <el-form-item label="核验方式">
          <el-select v-model="vf.verifyType" style="width:100%">
            <el-option label="人脸比对" value="FACE_COMPARE" />
            <el-option label="身份证 OCR" value="IDCARD_OCR" />
            <el-option label="政务数据核验" value="GOV_DATA" />
          </el-select></el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="vf.userName" /></el-form-item>
        <el-form-item label="人脸图片URL">
          <el-input v-model="vf.faceImgUrl" /></el-form-item>
        <el-form-item label="证件图片URL">
          <el-input v-model="vf.idcardImgUrl" /></el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="未通过实名核验的人员不能提交申请（后端硬校验）" />
      <template #footer>
        <el-button @click="verifyVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doVerify">提交核验</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

const tab = ref('person')
const loading = ref(false)
const saving = ref(false)
const orgId = ref(null)
/** 组织下拉选项（显示名称，内部传 ID） */
const orgOptions = ref([])
function orgNameOf(id) {
  const hit = orgOptions.value.find((o) => Number(o.id) === Number(id))
  return hit ? hit.orgName : (id ? id : '-')
}

/**
 * 组织下拉的显示文本：有上级的组织加层级缩进，便于在树形结构里辨认。
 * 后端 bp_iam_org 有 parent_id / org_path / org_level，是真正的树。
 */
function orgOptionLabel(o) {
  const level = Number(o.orgLevel || 1)
  const indent = '　'.repeat(Math.max(0, Math.min(level - 1, 4)))
  return indent + (o.orgName || o.orgCode || o.id)
}
async function loadOrgOptions() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = d.rows || d || []
  } catch (e) { orgOptions.value = [] }
}
const keyword = ref('')

// 人员
const persons = ref([])
const pTotal = ref(0)
const pQuery = reactive({ pageNum: 1, pageSize: 20 })
const personVisible = ref(false)
const pf = reactive({ personName: '', idCard: '', phone: '', orgId: null,
  householdType: 'URBAN', maritalStatus: 'SINGLE', education: '', employer: '',
  remark: '' })

// 保障档案
const profiles = ref([])
const gTotal = ref(0)
const gQuery = reactive({ pageNum: 1, pageSize: 20, keyword: '' })
const profileVisible = ref(false)
const profilePersonId = ref(null)
/** 临近到期天数（后端参数名 withinDays） */
const expiringDays = ref(30)
const gf = reactive({ personId: null, securityType: 'PUBLIC', familySize: 1,
  familyType: 'SINGLE', monthlyIncome: 0, assetDeclare: 0, hasHouse: 0,
  hasVehicle: 0 })
const recalcVisible = ref(false)
const ic = reactive({ lowLine: 1200, lowIncomeLine: 2400, middleLowLine: 4000 })
const exitVisible = ref(false)
const ex = reactive({ exitDate: '', exitReason: '' })
const currentProfile = ref(null)

// 实名核验
const verifies = ref([])
const vTotal = ref(0)
const vQuery = reactive({ pageNum: 1, pageSize: 20, keyword: '' })
const verifyVisible = ref(false)
const verifyPersonId = ref(null)
const vf = reactive({ personId: null, verifyType: 'FACE_COMPARE', userName: '',
  faceImgUrl: '', idcardImgUrl: '' })

function money(v) {
  const n = Number(v)
  return Number.isFinite(n) ? '¥ ' + n.toFixed(2) : '-'
}

async function loadPersons() {
  loading.value = true
  try {
    const d = await req.get('/persons', {
      params: { ...pQuery, keyword: keyword.value || undefined,
                orgId: orgId.value || undefined }
    })
    persons.value = d.rows || d || []
    pTotal.value = Number(d.total || persons.value.length || 0)
  } catch (e) { persons.value = []; pTotal.value = 0 } finally { loading.value = false }
}

async function loadProfiles() {
  loading.value = true
  try {
    const d = await req.get('/guarantee-profiles', { params: { ...gQuery } })
    profiles.value = d.rows || d || []
    gTotal.value = Number(d.total || profiles.value.length || 0)
  } catch (e) { profiles.value = []; gTotal.value = 0 } finally { loading.value = false }
}

async function loadVerifies() {
  loading.value = true
  try {
    const d = await req.get('/verify-records', { params: { ...vQuery } })
    verifies.value = d.rows || d || []
    vTotal.value = Number(d.total || verifies.value.length || 0)
  } catch (e) { verifies.value = []; vTotal.value = 0 } finally { loading.value = false }
}

function reloadAll() {
  loadPersons(); loadProfiles(); loadVerifies()
}

function onTab(name) {
  if (name === 'person') loadPersons()
  else if (name === 'profile') loadProfiles()
  else loadVerifies()
}

// ---------- 人员 ----------
const editTarget = ref(null)

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
  editTarget.value = null
  Object.assign(pf, { personName: '', idCard: '', phone: '', orgId: orgId.value,
    householdType: 'URBAN', maritalStatus: 'SINGLE', education: '', employer: '',
    remark: '' })
  personVisible.value = true
}
async function doCreatePerson() {
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
}
const statusVisible = ref(false)
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
}
async function removePerson(row) {
  await ElMessageBox.confirm(`确认删除人员「${row.personName}」？`, '删除确认',
    { type: 'warning' })
  await req.delete(`/persons/${row.id}`)
  ElMessage.success('已删除'); loadPersons()
}
async function queryByIdCard() {
  const { value } = await ElMessageBox.prompt('请输入完整身份证号', '按证件号查询')
  const d = await req.get('/persons/by-id-card', { params: { idCard: value } })
  if (d) {
    persons.value = [d]
    pTotal.value = 1
    ElMessage.success('已找到：' + (d.personName || d.id))
  } else {
    ElMessage.warning('未找到该证件号人员')
  }
}

// ---------- 保障档案 ----------
const profileEditMode = ref(false)

function openProfileFor(row) {
  profileEditMode.value = false
  gf.personId = Number(row.id)
  profileVisible.value = true
}

/** 编辑保障档案：回填已有值，保存时按 personId 覆盖 */

/** 把后端返回的对象/JSON 转成可读的「字段：值」列表 */
function readableResult(obj) {
  const LABEL = {
    incomeLevel: '收入档位', securityType: '保障类型', profileStatus: '档案状态',
    familySize: '家庭人口', familyType: '家庭结构', monthlyIncome: '月收入',
    perCapitaIncome: '人均月收入', assetDeclare: '资产申报', hasHouse: '名下有房',
    hasVehicle: '名下有车', qualifyDate: '资格认定日期', qualifyResult: '判定结果',
    failCount: '失败次数', failRate: '失败率', totalCount: '总次数',
    verifyType: '核验方式', count: '数量', reason: '原因', passCount: '通过次数'
  };
  const fmt = (v) => {
    if (v === null || v === undefined || v === '') return '—';
    if (v === 0 || v === 1) return v === 1 ? '是' : '否';
    if (typeof v === 'object') return Array.isArray(v) ? `${v.length} 条` : '—';
    return String(v);
  };
  const rows = [];
  const walk = (o, prefix) => {
    Object.keys(o || {}).forEach((k) => {
      // 内部标识类字段不展示（ID / 租户 / 时间戳）
      if (/^(id|tenantId|personId|createTime|updateTime|isDeleted)$/.test(k)) return;
      const v = o[k];
      const label = (prefix ? prefix + '.' : '') + (LABEL[k] || k);
      if (v && typeof v === 'object' && !Array.isArray(v)) walk(v, label);
      else rows.push(`${label}：${fmt(v)}`);
    });
  };
  walk(obj, '');
  return rows.length ? rows.join('<br/>') : '无数据';
}

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
}
async function doCreateProfile() {
  if (!gf.personId) { ElMessage.warning('请填写人员ID'); return }
  saving.value = true
  try {
    await req.post('/guarantee-profiles', { ...gf })
    ElMessage.success(profileEditMode.value ? '保障档案已更新' : '保障档案已建立')
    profileVisible.value = false; tab.value = 'profile'; loadProfiles()
  } finally { saving.value = false }
}
async function loadExpiring() {
  // 后端参数名是 withinDays；此前传 days 会被忽略，等于永远用默认值
  const d = await req.get('/guarantee-profiles/expiring', {
    params: { withinDays: expiringDays.value || undefined }
  })
  profiles.value = Array.isArray(d) ? d : (d.rows || [])
  gTotal.value = profiles.value.length
  ElMessage.success(`临近到期（${expiringDays.value} 天）：${profiles.value.length} 条`)
}
async function loadProfileByPerson() {
  if (!profilePersonId.value) { ElMessage.warning('请填写人员ID'); return }
  const d = await req.get(`/guarantee-profiles/person/${profilePersonId.value}`)
  profiles.value = d ? [d] : []
  gTotal.value = profiles.value.length
}
function openRecalc(row) {
  currentProfile.value = row
  recalcVisible.value = true
}
async function doRecalc() {
  saving.value = true
  try {
    const r = await req.post(
      `/guarantee-profiles/person/${currentProfile.value.personId}/recalc-income`,
      { ...ic })
    ElMessage.success('重算完成：' + (r?.incomeLevelAfter || r?.incomeLevel || '已更新'))
    recalcVisible.value = false; loadProfiles()
  } finally { saving.value = false }
}
async function qualify(row) {
  await ElMessageBox.confirm(
    '资格判定会综合收入档位、家庭人口、名下房产与车辆，确认执行？', '资格判定',
    { type: 'warning' })
  const r = await req.post(
    `/guarantee-profiles/person/${row.personId}/qualify`)
  ElMessageBox.alert(JSON.stringify(r, null, 2).slice(0, 500), '判定结果')
}
function exitProfile(row) {
  currentProfile.value = row
  ex.exitDate = new Date().toISOString().slice(0, 10)
  ex.exitReason = ''
  exitVisible.value = true
}
async function doExit() {
  if (!ex.exitDate) { ElMessage.warning('请选择退出日期'); return }
  saving.value = true
  try {
    await req.post(`/guarantee-profiles/person/${currentProfile.value.personId}/exit`,
      { ...ex })
    ElMessage.success('已退出保障')
    exitVisible.value = false; loadProfiles()
  } finally { saving.value = false }
}

// ---------- 实名核验 ----------
function openVerifyFor(row) {
  vf.personId = Number(row.id)
  vf.userName = row.personName || ''
  verifyVisible.value = true
}
async function doVerify() {
  if (!vf.personId) { ElMessage.warning('请填写人员ID'); return }
  saving.value = true
  try {
    const r = await req.post('/verify-records', { ...vf })
    ElMessage.success('核验完成：' + (Number(r?.verifyPass) === 1 ? '通过' : '未通过'))
    verifyVisible.value = false; tab.value = 'verify'; loadVerifies()
  } finally { saving.value = false }
}
async function loadFailStats() {
  const r = await req.get('/verify-records/fail-stats')
  ElMessageBox.alert(JSON.stringify(r, null, 2).slice(0, 600), '核验失败统计')
}
async function loadConclusion() {
  if (!verifyPersonId.value) { ElMessage.warning('请填写人员ID'); return }
  const r = await req.get(`/verify-records/person/${verifyPersonId.value}/conclusion`)
  ElMessageBox.alert(
    `结论：${r?.passed ? '通过' : '未通过'}\n最近核验：${r?.lastVerifyTime || '-'}\n原因：${r?.reason || '-'}`,
    '实名核验结论')
}

/** 清空「人员档案」tab 的筛选 */
function resetPersonQuery() {
  keyword.value = ''
  pQuery.pageNum = 1
  loadPersons()
}

/** 清空顶部全局筛选（组织 + 关键字）并刷新三个 tab */
function resetAllQuery() {
  orgId.value = null
  keyword.value = ''
  pQuery.pageNum = 1
  reloadAll()
}

onMounted(() => { loadOrgOptions(); reloadAll() })
</script>
