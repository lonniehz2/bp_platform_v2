<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">合同管理</h3>
        <el-input v-model="q.keyword" placeholder="合同号 / 承租人" clearable
                  style="width:180px" @keyup.enter="reload" />
        <el-select v-model="q.contractStatus" placeholder="状态" clearable
                   style="width:150px" @change="reload">
          <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
        </el-select>
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button @click="resetQuery">清空</el-button>
        <div class="spacer" />
        <el-button type="success" @click="openCreate">新建合同</el-button>
          <el-button type="primary" plain @click="openQuickSign"
                     data-testid="quick-sign">快捷签约</el-button>
        <el-button @click="expireDue">到期批量处理</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small" max-height="560">
        <el-table-column prop="contractNo" label="合同号" width="165" show-overflow-tooltip />
        <el-table-column prop="lesseeName" label="承租人" width="100" />
        <el-table-column prop="houseAddress" label="房屋" min-width="170" />
        <el-table-column label="租期" width="190">
          <template #default="{ row }">
            <span style="white-space:nowrap">{{ row.leaseStart }} ~ {{ row.leaseEnd }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="monthlyRent" label="月租" width="95" />
          <el-table-column prop="depositAmount" label="押金" width="90" />
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              {{ row.contractTypeLabel || enumLabel('contractType', row.contractType) }}
            </template>
          </el-table-column>
        <!-- 「到期」不再是独立列：租期已含起止日期，剩余天数并入状态列展示 -->
        <el-table-column label="状态" width="140">
          <template #default="{ row }">
            <el-tag size="small" :type="row.expiringSoon ? 'warning' : 'info'">
              {{ row.contractStatusLabel || row.contractStatus }}
            </el-tag>
            <span v-if="row.expiringSoon" class="muted" style="margin-left:4px;font-size:12px">
              剩 {{ row.daysToExpire }} 天
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="190">
          <template #default="{ row }">
            <el-button link type="primary" @click="openContractDetail(row)"
                       data-testid="contract-detail">详情</el-button>
            <el-button link type="warning" :disabled="row.contractStatus !== 'DRAFT'"
                       @click="openContractEdit(row)"
                       data-testid="contract-edit">编辑</el-button>
            <el-dropdown trigger="click" style="margin-left:8px">
              <el-button link type="primary">更多 ▾</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="openCohabitant(row)">同住人</el-dropdown-item>
                  <el-dropdown-item v-if="row.contractStatus === 'DRAFT'"
                                    @click="doSubmitSign(row)">提交待签</el-dropdown-item>
                  <el-dropdown-item v-if="row.contractStatus === 'PENDING_SIGN'"
                                    @click="doStartSigning(row)">开始签约</el-dropdown-item>
                  <el-dropdown-item v-if="row.contractStatus === 'SIGNING'"
                                    @click="openSign(row)">签约</el-dropdown-item>
                  <el-dropdown-item
                    v-if="row.contractStatus === 'EFFECTIVE' || row.contractStatus === 'RENEWING'"
                    @click="openRenew(row)">续签</el-dropdown-item>
                  <el-dropdown-item
                    v-if="row.contractStatus === 'EFFECTIVE' || row.contractStatus === 'RENEWING'"
                    divided @click="openTerminate(row)">终止</el-dropdown-item>
                  <el-dropdown-item
                    v-if="!['TERMINATED', 'EXPIRED', 'CANCELLED'].includes(row.contractStatus)"
                    divided @click="cancel(row)">取消合同</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="q.pageSize" :current-page="q.pageNum"
                     @current-change="(p) => { q.pageNum = p; load() }" />
    </div>

    <!-- 新建合同 ContractCreateCmd -->
    <el-dialog v-model="createVisible" title="新建合同" width="680px">
      <el-form :model="c" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="合同类型">
            <el-select v-model="c.contractType" style="width:100%">
              <el-option label="公租房" value="PUBLIC_RENTAL" />
              <el-option label="保租房" value="AFFORDABLE" />
              <el-option label="人才公寓" value="TALENT" />
              <el-option label="廉租房" value="LOW_RENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="出租组织ID" required>
            <el-input v-model="c.orgId" data-testid="c-org-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="出租方组织ID" required>
            <el-input v-model="c.lessorOrgId" data-testid="c-lessor-org-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="承租人ID" required>
            <el-input v-model="c.lesseePersonId" data-testid="c-lessee-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="承租人姓名">
            <el-input v-model="c.lesseeName" data-testid="c-lessee-name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="联系电话">
            <el-input v-model="c.lesseePhone" data-testid="c-lessee-phone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="证件号">
            <el-input v-model="c.lesseeIdCardMask" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="房源ID" required>
            <el-input v-model="c.houseId" data-testid="c-house-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="空间ID" required>
            <el-input v-model="c.spaceId" data-testid="c-space-id" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="房屋地址">
            <el-input v-model="c.houseAddress" data-testid="c-address" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="建筑面积">
            <el-input v-model.number="c.houseArea" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="起租日">
            <div data-testid="c-lease-start" style="width:100%">
              <el-date-picker v-model="c.leaseStart" type="date"
                              value-format="YYYY-MM-DD" style="width:100%" />
            </div>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="止租日">
            <div data-testid="c-lease-end" style="width:100%">
              <el-date-picker v-model="c.leaseEnd" type="date"
                              value-format="YYYY-MM-DD" style="width:100%" />
            </div>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="月租金" required>
            <el-input v-model.number="c.monthlyRent" data-testid="c-rent" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="租金单价" required>
            <el-input v-model.number="c.rentPrice" data-testid="c-rent-price" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="租金单位">
            <el-select v-model="c.rentUnit" style="width:100%" data-testid="c-rent-unit">
              <el-option label="按面积·月" value="AREA_MONTH" />
              <el-option label="按套·月" value="HOUSE_MONTH" />
              <el-option label="按床位·月" value="BED_MONTH" />
              <el-option label="按套·夜" value="HOUSE_NIGHT" />
              <el-option label="按床·夜" value="BED_NIGHT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="押金">
            <el-input v-model.number="c.depositAmount" data-testid="c-deposit" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="月补贴">
            <el-input v-model.number="c.subsidyAmount" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="付款周期">
            <el-select v-model="c.payCycle" style="width:100%">
              <el-option label="月付" value="MONTH" />
              <el-option label="季付" value="QUARTER" />
              <el-option label="半年付" value="HALF_YEAR" />
              <el-option label="年付" value="YEAR" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="付款日">
            <el-input v-model.number="c.payDay" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="关联配租单ID">
            <el-input v-model="c.allocationId" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="c.remark" type="textarea" :rows="2" />
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <el-alert type="warning" :closable="false" show-icon
                title="月租金/押金/补贴会按计费规则出账；关联配租单会做公示完成校验" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 签约 SignCmd -->
    <el-dialog v-model="signVisible" title="合同签约" width="480px">
      <el-form :model="sg" label-width="110px">
        <el-form-item label="签署方式">
          <el-select v-model="sg.signVendor" style="width:100%">
            <el-option label="线下纸质" value="OFFLINE" />
            <el-option label="电子签章" value="ESIGN" />
            <el-option label="CA证书" value="CA" />
          </el-select></el-form-item>
        <el-form-item label="签署文件URL">
          <el-input v-model="sg.signFileUrl" /></el-form-item>
        <el-form-item label="签署流程ID">
          <el-input v-model="sg.signFlowId" /></el-form-item>
        <el-form-item label="备注">
          <el-input v-model="sg.reason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="signVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSign">确认签约</el-button>
      </template>
    </el-dialog>

    <!-- 续签 RenewCmd -->
    <el-dialog v-model="renewVisible" title="合同续签" width="460px">
      <el-form :model="rn" label-width="110px">
        <el-form-item label="新止租日">
          <el-date-picker v-model="rn.newLeaseEnd" type="date"
                          value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="新月租金">
          <el-input v-model.number="rn.newMonthlyRent" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renewVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRenew">确认续签</el-button>
      </template>
    </el-dialog>

    <!-- 同住人（保障人口） -->
    <el-drawer v-model="cohabitantVisible" title="同住人（保障人口）" size="620px">
      <CohabitantPanel :contract-id="cohabitantContractId" />
    </el-drawer>

    <!-- 终止 -->
    <el-dialog v-model="termVisible" title="终止合同" width="460px">
      <el-form :model="tm" label-width="110px">
        <el-form-item label="终止类型">
          <el-select v-model="tm.terminateType" style="width:100%">
            <el-option label="协商终止" value="AGREEMENT" />
            <el-option label="违约终止" value="BREACH" />
            <el-option label="到期终止" value="EXPIRE" />
          </el-select></el-form-item>
        <el-form-item label="终止原因">
          <el-input v-model="tm.reason" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="termVisible = false">取消</el-button>
        <el-button type="danger" :loading="saving" @click="doTerminate">确认终止</el-button>
      </template>
    </el-dialog>
  </div>

    <!-- 合同详情 -->
    <el-dialog v-model="detailVisible" title="合同详情" width="820px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="合同号">{{ detail.contractNo }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          {{ detail.contractStatusLabel || enumLabel('contractStatus', detail.contractStatus) }}
        </el-descriptions-item>
        <el-descriptions-item label="合同类型">
          {{ detail.contractTypeLabel || enumLabel('contractType', detail.contractType) }}
        </el-descriptions-item>
        <el-descriptions-item label="承租人">{{ detail.lesseeName }}</el-descriptions-item>
        <el-descriptions-item label="证件号">{{ detail.lesseeIdCardMask }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detail.lesseePhone }}</el-descriptions-item>
        <el-descriptions-item label="房屋" :span="2">{{ detail.houseAddress }}</el-descriptions-item>
        <el-descriptions-item label="面积">{{ detail.houseArea }} ㎡</el-descriptions-item>
        <el-descriptions-item label="出租方">{{ detail.lessorOrgIdName }}</el-descriptions-item>
        <el-descriptions-item label="起租">{{ detail.leaseStart }}</el-descriptions-item>
        <el-descriptions-item label="止租">{{ detail.leaseEnd }}</el-descriptions-item>
        <el-descriptions-item label="租期">{{ detail.leaseMonths }} 个月</el-descriptions-item>
        <el-descriptions-item label="月租">{{ detail.monthlyRent }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ detail.depositAmount }}</el-descriptions-item>
        <el-descriptions-item label="已收">{{ detail.actualPay }}</el-descriptions-item>
        <el-descriptions-item label="补贴">{{ detail.subsidyAmount }}</el-descriptions-item>
        <el-descriptions-item label="支付周期">{{ detail.payCycle }}</el-descriptions-item>
        <el-descriptions-item label="签约时间">{{ detail.signTime }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detail.remark || '—' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer><el-button @click="detailVisible = false">关闭</el-button></template>
    </el-dialog>

    <!-- 编辑合同（仅草稿） -->
    <el-dialog v-model="editVisible" title="编辑合同条款（仅草稿可改）" width="620px">
      <el-alert type="warning" :closable="false" show-icon
                title="签约后修改金额或租期请走「合同变更」，此处仅限草稿" />
      <el-form :model="ef" label-width="100px" style="margin-top:12px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="月租">
            <el-input v-model="ef.monthlyRent" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="押金">
            <el-input v-model="ef.depositAmount" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="起租日">
            <el-date-picker v-model="ef.leaseStart" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="止租日">
            <el-date-picker v-model="ef.leaseEnd" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="支付周期">
            <el-select v-model="ef.payCycle" style="width:100%">
              <el-option label="月付" value="MONTH" />
              <el-option label="季付" value="QUARTER" />
              <el-option label="半年付" value="HALF_YEAR" />
              <el-option label="年付" value="YEAR" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="每月付款日">
            <el-input v-model="ef.payDay" type="number" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="ef.remark" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveContractEdit">保存</el-button>
      </template>
    </el-dialog>

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
</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { contractApi } from '@/api/modules'
import req from '@/api/request'
import CohabitantPanel from '@/components/CohabitantPanel.vue'
import PersonPicker from '@/components/PersonPicker.vue'

const statuses = ['DRAFT', 'PENDING_SIGN', 'EFFECTIVE', 'CHANGING', 'TERMINATED', 'EXPIRED']
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const q = reactive({ pageNum: 1, pageSize: 20, contractStatus: '', keyword: '' })

const createVisible = ref(false)
const signVisible = ref(false)
const renewVisible = ref(false)
const termVisible = ref(false)
const current = ref(null)
const cohabitantVisible = ref(false)
const cohabitantContractId = ref(null)

function openCohabitant(row) {
  cohabitantContractId.value = row.id
  cohabitantVisible.value = true
}

const c = reactive({ contractType: 'PUBLIC_RENTAL', orgId: 1, lessorOrgId: 1, lesseePersonId: null,
  lesseeName: '', lesseePhone: '', lesseeIdCardMask: '', houseId: null, spaceId: null,
  houseAddress: '', houseArea: null, leaseStart: '', leaseEnd: '', rentPrice: null,
  rentUnit: 'HOUSE_MONTH', monthlyRent: null, depositAmount: null, subsidyAmount: 0,
  payCycle: 'MONTH', payDay: 5, allocationId: null, remark: '' })
const sg = reactive({ signVendor: 'OFFLINE', signFileUrl: '', signFlowId: '', reason: '' })
const rn = reactive({ newLeaseEnd: '', newMonthlyRent: null })
const tm = reactive({ terminateType: 'AGREEMENT', reason: '' })

async function load() {
  loading.value = true
  try {
    const d = await contractApi.page({
      pageNum: q.pageNum, pageSize: q.pageSize,
      // 后端参数名为 status；contractStatus 会被忽略
      status: q.contractStatus || undefined,
      keyword: q.keyword || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}
function reload() { q.pageNum = 1; load() }

function openCreate() { createVisible.value = true }
async function doCreate() {
  // 必填项与后端 ContractCreateCmd 的 @NotNull 保持一致
  const missing = []
  if (!c.orgId) missing.push('出租组织ID')
  if (!c.lessorOrgId) missing.push('出租方组织ID')
  if (!c.lesseePersonId) missing.push('承租人ID')
  if (!c.houseId) missing.push('房源ID')
  if (!c.spaceId) missing.push('空间ID')
  if (!c.leaseStart) missing.push('起租日')
  if (!c.leaseEnd) missing.push('止租日')
  if (c.rentPrice == null) missing.push('租金单价')
  if (c.monthlyRent == null) missing.push('月租金')
  if (missing.length) {
    ElMessage.warning('请填写必填项：' + missing.join('、')); return
  }
  saving.value = true
  try {
    await contractApi.create({ ...c })
    ElMessage.success('合同已创建')
    createVisible.value = false; load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}

function openSign(row) { current.value = row; signVisible.value = true }

async function doSubmitSign(row) {
  saving.value = true
  try {
    await contractApi.submitSign(row.id)
    ElMessage.success('已提交待签')
    load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}

async function doStartSigning(row) {
  saving.value = true
  try {
    await contractApi.startSigning(row.id, { signVendor: 'OFFLINE' })
    ElMessage.success('已进入签约中')
    load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}

async function doSign() {
  saving.value = true
  try {
    await contractApi.sign(current.value.id, { ...sg })
    ElMessage.success('签约成功')
    signVisible.value = false; load()
  } finally { saving.value = false }
}

function openRenew(row) {
  current.value = row
  rn.newLeaseEnd = row.leaseEnd; rn.newMonthlyRent = row.monthlyRent
  renewVisible.value = true
}
async function doRenew() {
  saving.value = true
  try {
    await contractApi.renew(current.value.id, { ...rn })
    ElMessage.success('续签成功')
    renewVisible.value = false; load()
  } finally { saving.value = false }
}

function openTerminate(row) {
  current.value = row; tm.reason = ''; termVisible.value = true
}
async function doTerminate() {
  if (!tm.reason) { ElMessage.warning('请填写终止原因'); return }
  saving.value = true
  try {
    await contractApi.terminate(current.value.id, { ...tm })
    ElMessage.success('合同已终止')
    termVisible.value = false; load()
  } finally { saving.value = false }
}

async function cancel(row) {
  const { value } = await ElMessageBox.prompt('请输入取消原因', '取消合同')
  await contractApi.cancel(row.id, value)
  ElMessage.success('已取消'); load()
}

async function expireDue() {
  const r = await contractApi.expireDue()
  ElMessage.success('到期处理完成：' + (r?.count ?? r ?? '已执行'))
  load()
}

const q0 = JSON.parse(JSON.stringify(q))
function resetQuery() {
  Object.assign(q, q0)
  reload()
}

// 待办中心「待签合同」跳转过来时带 pending=1（待签约状态）
if (/pending=1/.test(window.location.hash)) {
  q.contractStatus = 'PENDING_SIGN'
}

/** 合同详情 / 编辑 */
const detailVisible = ref(false)
const detail = ref({})
const editVisible = ref(false)
const editingId = ref(null)
const ef = reactive({ monthlyRent: null, depositAmount: null, leaseStart: '', leaseEnd: '',
  payCycle: 'MONTH', payDay: 5, remark: '' })

async function openContractDetail(row) {
  // 列表已有大部分字段，再取一次详情确保完整
  try {
    const d = await req.get(`/contracts/${row.id}`)
    detail.value = d || row
  } catch (e) { detail.value = row }
  detailVisible.value = true
}

function openContractEdit(row) {
  editingId.value = row.id
  ef.monthlyRent = Number(row.monthlyRent || 0)
  ef.depositAmount = Number(row.depositAmount || 0)
  ef.leaseStart = row.leaseStart || ''
  ef.leaseEnd = row.leaseEnd || ''
  ef.payCycle = row.payCycle || 'MONTH'
  ef.payDay = Number(row.payDay || 5)
  ef.remark = row.remark || ''
  editVisible.value = true
}

async function saveContractEdit() {
  saving.value = true
  try {
    await req.put(`/contracts/${editingId.value}`, { ...ef })
    ElMessage.success('合同条款已更新')
    editVisible.value = false
    load()
  } finally { saving.value = false }
}


/** 快捷签约（存量人员+空置房源直接出合同） */
const quickSignVisible = ref(false)
const vacantHouses = ref([])
const houseLoading = ref(false)
const route = useRoute()
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


/** 从公示中签名单跳转进来：预填并打开快捷签约 */
function prefillQuickSign(query) {
  if (!query || !query.personId) return
  openQuickSign()
  qf.personId = String(query.personId)
  if (query.houseId) {
    qf.houseId = String(query.houseId)
    req.get(`/houses/${query.houseId}`).then((h) => {
      if (h) vacantHouses.value = [{ ...h }]
    }).catch(() => {})
  }
}

onMounted(() => {
  load()
  prefillQuickSign(route.query)
})
</script>
