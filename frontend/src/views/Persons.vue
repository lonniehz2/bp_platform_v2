<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('person.title') }}</h3>
      <el-tag size="small" type="info">{{ t('misc7.personFlow') }}</el-tag>
      <div class="spacer" />
      <el-select v-model="orgId" filterable clearable :placeholder="t('person.allOrg')"
                 style="width:220px" data-testid="person-org-filter">
        <el-option :label="t('person.allOrg')" :value="null" />
        <el-option v-for="o in orgOptions" :key="o.id"
                   :label="orgOptionLabel(o)" :value="o.id" />
      </el-select>
      <el-checkbox v-model="includeChildren" :disabled="!orgId"
                   data-testid="person-org-children">{{ t('misc7.includeChildren') }}</el-checkbox>
      <el-button type="primary" @click="reloadAll">{{ t('person.search') }}</el-button>
      <el-button @click="resetAllQuery">{{ t('person.reset') }}</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon
              :title="t('misc7.orderTip')"
              style="margin-bottom:12px" />

    <el-tabs v-model="tab" @tab-change="onTab">
      <!-- ============ 人员档案 ============ -->
      <el-tab-pane :label="t('person.tabPerson')" name="person">
        <div class="toolbar">
          <el-input v-model="keyword" :placeholder="t('person.keyword')" clearable
                    style="width:190px" @keyup.enter="loadPersons" />
          <el-button @click="loadPersons">{{ t('person.search') }}</el-button>
          <el-button @click="resetPersonQuery">{{ t('person.reset') }}</el-button>
          <el-button @click="queryByIdCard">{{ t('person.exact') }}</el-button>
          <div class="spacer" />
          <el-button type="success" @click="openPerson">{{ t('person.add') }}</el-button>
        </div>
        <el-table :data="persons" v-loading="loading" border size="small" :empty-text="t('misc.emptyDefault')">
          <el-table-column prop="id" :label="t('person.id')" width="190" />
        <el-table-column prop="personName" :label="t('person.name')" width="110" />
          <el-table-column :label="t('person.org')" min-width="160">
            <template #default="{ row }">{{ orgNameOf(row.orgId) }}</template>
          </el-table-column>
          <el-table-column prop="idCardMask" :label="t('person.idCard')" width="190">
            <template #default="{ row }">{{ row.idCard || row.idCardMask || '-' }}</template>
          </el-table-column>
          <el-table-column prop="phoneMask" :label="t('person.phone')" width="140" />
        <el-table-column :label="t('person.verifyStatus')" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.verifyStatus === 'VERIFIED' ? 'success' : 'info'">
              {{ enumLabel('verifyStatus', row.verifyStatus) }}
            </el-tag>
          </template>
        </el-table-column>
          <el-table-column :label="t('person.household')" width="90">
            <template #default="{ row }">{{ enumLabel('householdType', row.householdType) }}</template>
          </el-table-column>
          <el-table-column :label="t('person.marriage')" width="90">
            <template #default="{ row }">{{ enumLabel('maritalStatus', row.maritalStatus) }}</template>
          </el-table-column>
          <el-table-column prop="personStatus" :label="t('person.status')" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.personStatus === 'NORMAL' ? 'success'
                : (row.personStatus === 'FROZEN' ? 'warning' : 'info')">
                {{ row.personStatusLabel || enumLabel('personStatus', row.personStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('person.actions')" width="330" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEdit(row)">{{ t('person.edit') }}</el-button>
              <el-button link type="primary" @click="changeStatus(row)">{{ t('person.changeStatus') }}</el-button>
              <el-button link @click="openProfileFor(row)">{{ t('person.profile') }}</el-button>
              <el-button link :disabled="row.verifyStatus === 'VERIFIED'"
                         @click="openVerifyFor(row)">{{ t('misc7.verifyButton') }}</el-button>
              <el-button link type="danger" @click="removePerson(row)">{{ t('person.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                       :total="+pTotal || 0" :page-size="pQuery.pageSize"
                       :current-page="pQuery.pageNum"
                       @current-change="(p) => { pQuery.pageNum = p; loadPersons() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pQuery.pageSize = s; pQuery.pageNum = 1; loadPersons() }" />
      </el-tab-pane>

      <!-- ============ 保障档案 ============ -->
      <el-tab-pane :label="t('person.tabProfile')" name="profile">
        <div class="toolbar">
          <el-button type="success" @click="profileVisible = true">{{ t('person.createProfile') }}</el-button>
          <el-button @click="loadExpiring">{{ t('person.expiring') }}</el-button>
          <el-input v-model.number="expiringDays" :placeholder="t('person.days')" style="width:90px"
                    data-testid="expiring-days" @keyup.enter="loadExpiring" />
          <div class="spacer" />
          <PersonPicker v-model="profilePersonId" width="260px"
                        testid="profile-filter-person" />
          <el-button type="primary" @click="loadProfileByPerson">{{ t('person.view') }}</el-button>
          <el-button @click="profilePersonId = null; loadProfiles()">{{ t('person.all') }}</el-button>
        </div>
        <el-alert type="info" :closable="false" show-icon
                  :title="t('misc7.qualifyTip')"
                  style="margin-bottom:10px" />
        <el-table :data="profiles" v-loading="loading" border size="small">
          <el-table-column :label="t('person.target')" width="230">
            <template #default="{ row }">
              <div>{{ row.personName || row.personId }}</div>
              <div class="muted" style="font-size:12px">
                {{ row.phoneMask || '-' }}　{{ row.idCardMask || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="t('person.securityType')" width="110">
            <template #default="{ row }">
              {{ row.securityTypeLabel || enumLabel('securityType', row.securityType) }}
            </template>
          </el-table-column>
          <el-table-column prop="familySize" :label="t('person.familySize')" width="100" />
          <el-table-column prop="monthlyIncome" :label="t('person.monthlyIncome')" width="110">
            <template #default="{ row }">{{ money(row.monthlyIncome) }}</template>
          </el-table-column>
          <el-table-column :label="t('person.incomeLevel')" width="130">
            <template #default="{ row }">
              <el-tag v-if="row.incomeLevelLabel || row.incomeLevel" size="small">
                {{ row.incomeLevelLabel || enumLabel('incomeLevel', row.incomeLevel) }}
              </el-tag>
              <span v-else class="muted">{{ t('misc7.unassessed') }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('person.status')" width="100">
            <template #default="{ row }">{{ row.profileStatusLabel || enumLabel('profileStatus', row.profileStatus) }}</template>
          </el-table-column>
          <el-table-column :label="t('person.actions')" width="300" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openProfileEdit(row)">{{ t('person.edit') }}</el-button>
              <el-button link type="primary" @click="openRecalc(row)">{{ t('person.recalc') }}</el-button>
              <el-button link type="success" @click="qualify(row)">{{ t('person.qualify') }}</el-button>
              <el-button link type="danger" :disabled="row.profileStatus === 'EXITED'"
                         :title="row.profileStatus === 'EXITED' ? t('misc7.exitedTip') : ''"
                         @click="exitProfile(row)">{{ t('misc7.exit') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                       :total="+gTotal || 0" :page-size="gQuery.pageSize"
                       :current-page="gQuery.pageNum"
                       @current-change="(p) => { gQuery.pageNum = p; loadProfiles() }" />
      </el-tab-pane>

      <!-- ============ 实名核验 ============ -->
      <el-tab-pane :label="t('person.tabVerify')" name="verify">
        <div class="toolbar">
          <el-button type="success" @click="verifyVisible = true">{{ t('person.startVerify') }}</el-button>
          <el-button @click="loadFailStats">{{ t('person.failStats') }}</el-button>
          <div class="spacer" />
          <PersonPicker v-model="verifyPersonId" width="260px"
                        testid="verify-filter-person" />
          <el-button type="primary" @click="loadConclusion">{{ t('person.conclusion') }}</el-button>
          <el-button @click="verifyPersonId = null; loadVerifies()">{{ t('person.all') }}</el-button>
        </div>
        <el-table :data="verifies" v-loading="loading" border size="small">
          <el-table-column :label="t('person.verifyTarget')" width="240">
            <template #default="{ row }">
              <div>{{ row.personName || row.personId }}</div>
              <div class="muted" style="font-size:12px">
                {{ row.phoneMask || '-' }}　{{ row.idCardMask || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="t('person.verifyMethod')" width="130">
            <template #default="{ row }">
              {{ enumLabel('verifyType', row.verifyType) || row.verifyType }}
            </template>
          </el-table-column>
          <el-table-column :label="t('person.result')" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="Number(row.verifyPass) === 1 ? 'success' : 'danger'">
                {{ Number(row.verifyPass) === 1 ? t('misc7.pass') : t('misc7.notPass') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="faceScore" :label="t('person.faceScore')" width="100" />
          <el-table-column prop="responseCode" :label="t('person.responseCode')" width="100" />
          <el-table-column prop="verifyTime" :label="t('person.verifyTime')" width="170" />
          <el-table-column :label="t('person.actions')" width="200" fixed="right">
            <template #default="{ row }">
              <el-button v-if="Number(row.verifyPass) !== 1" link type="primary"
                         @click="openVerifyFor(row)">实名核验</el-button>
              <el-button v-if="Number(row.verifyPass) !== 1" link type="success"
                         @click="manualPass(row.personId)">核验通过</el-button>
              <span v-else class="muted">已通过</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                       :total="+vTotal || 0" :page-size="vQuery.pageSize"
                       :current-page="vQuery.pageNum"
                       @current-change="(p) => { vQuery.pageNum = p; loadVerifies() }" />
      </el-tab-pane>
    </el-tabs>

    <!-- 新增人员 PersonCreateCmd -->
    <el-dialog v-model="personVisible"
               :title="editTarget ? t('person.editTitle') : t('person.newTitle')" width="620px">
      <el-form :model="pf" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('person.name')" required>
            <el-input v-model="pf.personName" data-testid="person-name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('person.idCard')">
            <el-input v-model="pf.idCard" :disabled="!!editTarget"
                      :placeholder="t('person.idCardHint')" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('person.phone')">
            <el-input v-model="pf.phone" data-testid="person-phone"
                      :placeholder="t('person.phoneHint')" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="所属组织">
            <el-select v-model="pf.orgId" filterable clearable style="width:100%"
                       :placeholder="t('person.orgHint')" data-testid="person-org">
              <el-option v-for="o in orgOptions" :key="o.id"
                         :label="o.orgName" :value="String(o.id)" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('person.householdType')">
            <el-select v-model="pf.householdType" style="width:100%">
              <el-option :label="t('person.urban')" value="URBAN" />
              <el-option :label="t('person.rural')" value="RURAL" />
              <el-option :label="t('person.other')" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('person.maritalStatus')">
            <el-select v-model="pf.maritalStatus" style="width:100%">
              <el-option :label="t('person.single')" value="SINGLE" />
              <el-option :label="t('person.married')" value="MARRIED" />
              <el-option :label="t('person.divorced')" value="DIVORCED" />
              <el-option :label="t('person.widowed')" value="WIDOWED" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('person.education')">
            <el-input v-model="pf.education" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('person.employer')">
            <el-input v-model="pf.employer" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item :label="t('person.remark')">
            <el-input v-model="pf.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="personVisible = false">{{ t('person.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreatePerson">{{ t('person.save') }}</el-button>
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
          <el-col :span="12"><el-form-item label="人员" required>
            <PersonPicker v-model="gf.personId" width="100%"
                          testid="profile-person-picker" /></el-form-item></el-col>
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
        <el-form-item label="人员" required>
          <PersonPicker v-model="vf.personId" width="260px" testid="verify-person-picker" />
        </el-form-item>
        <el-form-item label="核验方式">
          <el-select v-model="vf.verifyType" style="width:100%">
            <el-option label="人脸比对" value="FACE_COMPARE" />
            <el-option label="身份证 OCR" value="IDCARD_OCR" />
            <el-option label="政务数据核验" value="GOV_DATA" />
          </el-select></el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="vf.userName" /></el-form-item>
        <el-form-item label="人脸照片">
          <div style="width:100%">
            <el-upload :action="uploadAction" :headers="uploadHeaders" name="file"
                       :show-file-list="false" accept="image/*"
                       :on-success="(r) => { vf.faceImgUrl = fileUrlOf(r) }"
                       :on-error="() => ElMessage.error('上传失败')">
              <el-button size="small">本地上传</el-button>
            </el-upload>
            <div class="muted" style="font-size:12px;margin-top:4px">
              {{ vf.faceImgUrl || '未上传（也可粘贴外部 URL）' }}
            </div>
            <el-input v-model="vf.faceImgUrl" placeholder="或粘贴图片 URL" size="small" />
          </div>
        </el-form-item>
        <el-form-item label="证件照片">
          <div style="width:100%">
            <el-upload :action="uploadAction" :headers="uploadHeaders" name="file"
                       :show-file-list="false" accept="image/*"
                       :on-success="(r) => { vf.idcardImgUrl = fileUrlOf(r) }"
                       :on-error="() => ElMessage.error('上传失败')">
              <el-button size="small">本地上传</el-button>
            </el-upload>
            <div class="muted" style="font-size:12px;margin-top:4px">
              {{ vf.idcardImgUrl || '未上传（也可粘贴外部 URL）' }}
            </div>
            <el-input v-model="vf.idcardImgUrl" placeholder="或粘贴图片 URL" size="small" />
          </div>
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="未通过实名核验的人员不能提交申请（后端硬校验）" />
      <template #footer>
        <el-button @click="verifyVisible = false">取消</el-button>
        <el-button type="success" :loading="saving" @click="doManualPass">
          演示：核验通过
        </el-button>
        <el-button type="primary" :loading="saving" @click="doVerify">提交核验</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import req, { getToken, getTenant } from '@/api/request'
import PersonPicker from '@/components/PersonPicker.vue'
import { enumLabel } from '@/constants/enums'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const TABS = ['person', 'profile', 'verify']
const tab = ref(TABS.includes(route.params.tab) ? route.params.tab : 'person')
// 侧边栏点不同子项时切换 tab；页内切 tab 时同步地址
watch(() => route.params.tab, (v) => {
  if (v && TABS.includes(v) && v !== tab.value) { tab.value = v; onTab(v) }
})
watch(tab, (v) => {
  if (route.params.tab !== v) router.replace('/persons/' + v)
})
const loading = ref(false)
const saving = ref(false)
const orgId = ref(null)
/** 组织筛选是否包含下级组织 */
const includeChildren = ref(false)
/** 组织下拉选项（显示名称，内部传 ID） */
const orgOptions = ref([])
function orgNameOf(id) {
  const hit = orgOptions.value.find((o) => String(o.id) === String(id))
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
const gQuery = reactive({ pageNum: 1, pageSize: 20, personId: '' })
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
const vQuery = reactive({ pageNum: 1, pageSize: 20, personId: '' })
const verifyVisible = ref(false)
// 核验照片上传：走后端 /files/upload，成功回填可访问 URL
const uploadAction = '/api/v1/files/upload?bizType=PERSON_VERIFY'
const uploadHeaders = {
  Authorization: `Bearer ${getToken()}`,
  'X-Tenant-Id': getTenant()
}
function fileUrlOf(r) {
  const f = (r && r.data) || {}
  return f.id ? `/api/v1/files/${f.id}/download` : ''
}
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
    orgId: row.orgId ? String(row.orgId) : null,
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
  gf.personId = String(row.id)
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
    personId: String(row.personId || row.id),
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
    '将按档案事实判定资格：\n· 收入档位不能是「普通」（超中低收入线）\n· 名下有房需在备注说明例外依据\n· 人才认定需在有效期内\n\n通过后档案置「已通过」，有效期 1 年；不通过会逐条提示原因。确认执行？',
    '资格判定', { type: 'warning', customStyle: { whiteSpace: 'pre-line' } })
  const r = await req.post(
    `/guarantee-profiles/person/${row.personId}/qualify`)
  // 后端返回保障档案实体，这里转成中文结果，避免直接抛 JSON
  const lines = [
    `人员：${r?.personId || row.personId}`,
    `档案状态：${profileStatusText(r?.profileStatus)}`,
    `收入档位：${enumLabel('incomeLevel', r?.incomeLevel) || r?.incomeLevel || '—'}`,
    `家庭人口：${r?.familySize ?? '—'}`,
    `人均收入：${r?.perCapitaIncome ?? '—'} 元/月`,
    `资格认定日期：${r?.qualifyDate || '—'}`,
    `资格有效期至：${r?.qualifyExpire || '—'}`
  ]
  ElMessageBox.alert(lines.join('\n'), '资格判定结果',
    { customStyle: { whiteSpace: 'pre-line' } })
  loadProfiles()
}

function profileStatusText(s) {
  return { DRAFT: '草稿', SUBMITTED: '已提交', QUALIFIED: '已通过', IN_RESIDENCE: '在保',
    EXITED: '已退出' }[s] || s || '—'
}
function exitProfile(row) {
  if (row.profileStatus === 'EXITED') {
    ElMessage.info('该人员已退出保障')
    return
  }
  currentProfile.value = row
  ex.exitDate = new Date().toISOString().slice(0, 10)
  ex.exitReason = ''
  exitVisible.value = true
}
async function doExit() {
  if (!ex.exitDate) { ElMessage.warning('请选择退出日期'); return }
  await ElMessageBox.confirm(
    '退出后：\n· 档案状态置「已退出」\n· 该人员自动退出轮候队列（含已中签未配租）\n· 不能再新增申请或进入轮候\n\n历史记录保留可查，确认退出？',
    '退出保障', { type: 'warning', customStyle: { whiteSpace: 'pre-line' } })
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
  vf.personId = String(row.id)
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

/** 演示用：写入一条人工核验通过记录（同时把人员置为已实名） */
async function manualPass(personId) {
  const pid = personId || vf.personId
  if (!pid) { ElMessage.warning('请选择人员'); return }
  await ElMessageBox.confirm(
    '将以「人工核验」方式记录一次通过结果，并把人员实名状态置为已通过。确认？',
    '核验通过', { type: 'warning' })
  saving.value = true
  try {
    await req.post('/verify-records', {
      personId: pid,
      verifyType: 'MANUAL',
      userName: vf.userName || null,
      faceResult: '1',
      citizenResult: '0',
      responseCode: '0',
      resultCode: '0',
      faceScore: 100,
      rawResponse: '{"source":"manual-demo","remark":"演示：人工核验通过"}'
    })
    ElMessage.success('已记录核验通过，人员实名状态已更新')
    verifyVisible.value = false
    tab.value = 'verify'
    loadVerifies(); loadPersons()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  } finally { saving.value = false }
}

async function doManualPass() { await manualPass(vf.personId) }
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
