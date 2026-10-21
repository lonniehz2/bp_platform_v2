# -*- coding: utf-8 -*-
"""重新生成 12 个配置驱动页面：加入写操作表单（字段取自真实 Cmd record）"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend\src\views'

TPL = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{TITLE}}</h3>
      <el-tag v-if="TAG" size="small" type="info">{{TAG}}</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字/ID" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
{{ACTIONS_BAR}}
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="HINT" style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><pre class="raw">{{ '{{' }} JSON.stringify(row, null, 2) {{ '}}' }}</pre></template>
      </el-table-column>
{{COLUMNS}}
      <el-table-column label="操作" :width="ROWACTIONS ? 210 : 110" fixed="right">
        <template #default="{ row }">
{{ROWACTION_BTNS}}
          <el-button link @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <!-- 写操作表单（字段按后端 Cmd 定义配置） -->
    <el-dialog v-model="formVisible" :title="formTitle" width="560px">
      <el-form :model="model" label-width="120px">
        <el-form-item v-for="f in fields" :key="f.key" :label="f.label">
          <el-input v-if="f.type === 'text'" v-model="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'textarea'" type="textarea" :rows="3"
                    v-model="model[f.key]" :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'number'" v-model.number="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-date-picker v-else-if="f.type === 'date'" v-model="model[f.key]"
                          type="date" value-format="YYYY-MM-DD" style="width:100%" />
          <el-select v-else-if="f.type === 'select'" v-model="model[f.key]"
                     style="width:100%">
            <el-option v-for="o in f.options" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>
          <el-switch v-else-if="f.type === 'bool'" v-model="model[f.key]" />
        </el-form-item>
      </el-form>
      <el-alert v-if="formNote" :closable="false" show-icon type="warning"
                :title="formNote" style="margin-top:8px" />
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="明细（原始数据）" size="520px">
      <pre class="raw">{{ '{{' }} JSON.stringify(detail, null, 2) {{ '}}' }}</pre>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { {{API}} } from '@/api/modules'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const detailVisible = ref(false)
const detail = ref(null)

const formVisible = ref(false)
const formTitle = ref('')
const formNote = ref('')
const fields = {{FIELDS_JSON}}
const model = reactive({})
let submitFn = null
{{STATE}}

async function load() {
  loading.value = true
  try {
    const data = await {{API}}.{{METHOD}}({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined{{PARAM_EXTRA}}
    })
    rows.value = data.rows || data || []
    total.value = Number(data.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}

function reload() { pageNum.value = 1; load() }
function openDetail(row) { detail.value = row; detailVisible.value = true }

function openForm(title, fieldDefs, fn, preset = {}, note = '') {
  formTitle.value = title
  formNote.value = note
  Object.keys(model).forEach((k) => delete model[k])
  fieldDefs.forEach((f) => { model[f.key] = preset[f.key] ?? f.default ?? '' })
  submitFn = fn
  formVisible.value = true
}

async function submit() {
  saving.value = true
  try {
    await submitFn({ ...model })
    ElMessage.success('操作成功')
    formVisible.value = false
    load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}
{{FUNCS}}

onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
'''

S = lambda v, l: "{ value: '%s', label: '%s' }" % (v, l)

CFG = [
    dict(file='Persons', title='保障对象', tag='人员档案', api='personApi',
         method='page',
         cols=[('personName', '姓名', 120), ('idCardMask', '证件(脱敏)', 160),
               ('phone', '电话', 130), ('personStatus', '状态', 100)],
         hint='人员由申请或导入建立；保障专有属性在「保障档案」维护。'
              '写操作需后端提供 PersonCreateCmd 字段后补齐',
         bar='', rowbtns='', funcs=''),

    dict(file='Spaces', title='空间层级', tag='小区→楼栋→单元→楼层→房→床',
         api='spaceApi', method='page',
         cols=[('spaceName', '空间名称', 160), ('spaceType', '类型', 110),
               ('pathCode', '路径编码', 150)],
         hint='层级 AREA/BUILDING/UNIT/FLOOR/ROOM/BED；path_code 每级 2 位。'
              '空间由资产初始化建立，写操作按后端接口补齐',
         bar='', rowbtns='', funcs=''),

    dict(file='Terminations', title='退租管理', tag='', api='terminationApi',
         method='page',
         cols=[('terminationNo', '退租单号', 170), ('contractId', '合同', 130),
               ('terminationType', '类型', 120), ('terminationStatus', '状态', 110)],
         hint='过渡期月数与租金倍率由系统参数控制（默认 3 个月 / 1.5 倍）',
         bar='''      <el-button type="success" @click="openCreate">新建退租</el-button>''',
         rowbtns='''          <el-button link type="primary" @click="approve(row)">审批</el-button>''',
         fields=[('contractId', '合同ID', 'number'), ('houseId', '房源ID', 'number'),
                 ('personId', '人员ID', 'number'),
                 ('terminationType', '退租类型', 'select',
                  [('NORMAL', '正常退租'), ('EXPEL', '违规清退'),
                   ('EXPIRE', '到期不续'), ('EXCHANGE', '换房退出')]),
                 ('planExitDate', '计划退出日', 'date'),
                 ('exitReason', '退出原因', 'textarea'),
                 ('transitionMonths', '过渡期(月)', 'number')],
         funcs='''
function openCreate() {
  openForm('新建退租单', fields, (m) => terminationApi.create(m),
    { terminationType: 'NORMAL' },
    '提交后按流程审批；违规清退会影响信用惩戒')
}
async function approve(row) {
  await ElMessageBox.confirm('确认审批通过该退租单？', '提示', { type: 'warning' })
  await terminationApi.approve(row.id, {})
  ElMessage.success('已审批')
  load()
}'''),

    dict(file='Appeals', title='申诉管理', tag='救济通道', api='appealApi',
         method='page',
         cols=[('appealNo', '申诉号', 170), ('bizType', '业务类型', 130),
               ('appealStatus', '状态', 110), ('deadlineTime', '申诉期限', 170)],
         hint='申诉期限默认 10 天（系统参数可配）；异议成立会反向回写原业务',
         bar='''      <el-button type="success" @click="openCreate">发起申诉</el-button>''',
         rowbtns='', fields=[
             ('bizType', '业务类型', 'select',
              [('ANNUAL_REVIEW', '年度核查'), ('EXIT', '退出决定'),
               ('PUBLICITY', '公示异议')]),
             ('bizId', '业务单据ID', 'number'), ('personId', '人员ID', 'number'),
             ('orgId', '组织ID', 'number'),
             ('appealType', '申诉类型', 'text'),
             ('appealReason', '申诉理由', 'textarea'),
             ('appealEvidence', '证据材料', 'textarea'),
             ('daysFromNow', '申诉期限(天)', 'number')],
         funcs='''
function openCreate() {
  openForm('发起申诉', fields, (m) => appealApi.create(m), { daysFromNow: 10 },
    '超过申诉期限将无法受理')
}'''),

    dict(file='Credits', title='信用与惩戒', tag='', api='creditApi',
         method='page',
         cols=[('personId', '人员', 120), ('violationType', '违规类型', 150),
               ('sanctionType', '惩戒措施', 150), ('banEndDate', '限制至', 120)],
         hint='严重违规默认限制申请 5 年、一般 1 年（系统参数可配）；惩戒会真正阻止申请',
         bar='''      <el-button type="danger" @click="openCreate">新增惩戒</el-button>''',
         rowbtns='''          <el-button link type="warning" @click="revoke(row)">撤销</el-button>''',
         fields=[('personId', '人员ID', 'number'),
                 ('violationType', '违规类型', 'select',
                  [('FALSE_INFO', '提供虚假信息'), ('SUBLEASE', '转租出借'),
                   ('ARREARS', '恶意欠租'), ('VACANT', '长期空置')]),
                 ('violationDesc', '违规描述', 'textarea'),
                 ('evidenceUrl', '证据URL', 'text'),
                 ('sanctionType', '惩戒措施', 'select',
                  [('BAN_APPLY', '限制申请'), ('TERMINATE', '终止资格'),
                   ('CREDIT_PLATFORM', '推送信用平台')]),
                 ('banYears', '限制年限', 'number'),
                 ('legalDocNo', '法律文书号', 'text'),
                 ('pushToPlatform', '推送信用平台', 'bool'),
                 ('remark', '备注', 'textarea')],
         funcs='''
function openCreate() {
  openForm('新增信用惩戒', fields, (m) => creditApi.penalize(m),
    { violationType: 'FALSE_INFO', sanctionType: 'BAN_APPLY', banYears: 5,
      pushToPlatform: false },
    '严重违规默认 5 年；该惩戒会立即阻止该人员的申请')
}
async function revoke(row) {
  const { value } = await ElMessageBox.prompt('请输入撤销原因', '撤销惩戒')
  await creditApi.restore(row.id, value)
  ElMessage.success('已撤销')
  load()
}'''),

    dict(file='Exchanges', title='同租期限换房', tag='', api='exchangeApi',
         method='page',
         cols=[('exchangeNo', '换房单号', 170), ('oldContractId', '原合同', 130),
               ('newHouseId', '新房屋', 130), ('exchangeStatus', '状态', 110)],
         hint='同一租期限换 1 次；应换不换按 1.5 倍计租（均可配）',
         bar='''      <el-button type="success" @click="openCreate">发起换房</el-button>''',
         rowbtns='', fields=[
             ('personId', '人员ID', 'number'), ('oldContractId', '原合同ID', 'number'),
             ('oldHouseId', '原房源ID', 'number'),
             ('newHouseId', '新房源ID', 'number'),
             ('exchangeType', '换房类型', 'text'),
             ('exchangeReason', '换房原因', 'textarea'),
             ('familySizeAfter', '换后人口', 'number'),
             ('forceExchange', '强制换房', 'bool')],
         funcs='''
function openCreate() {
  openForm('发起换房', fields, (m) => exchangeApi.create(m),
    { forceExchange: false },
    '会生成新合同并终止原合同，房源同步互换')
}'''),

    dict(file='Complaints', title='投诉工单', tag='', api='complaintApi',
         method='page',
         cols=[('complaintNo', '投诉号', 170), ('complaintType', '类型', 130),
               ('complaintStatus', '状态', 110), ('createTime', '受理时间', 170)],
         hint='投诉可转工单处理；处理过程留痕',
         bar='''      <el-button type="success" @click="openCreate">登记投诉</el-button>''',
         rowbtns='', fields=[
             ('complaintType', '投诉类型', 'text'), ('source', '来源', 'text'),
             ('title', '标题', 'text'), ('content', '内容', 'textarea'),
             ('images', '图片URL', 'text'), ('orgId', '组织ID', 'number'),
             ('personId', '涉及人员', 'number'),
             ('submitterName', '提交人', 'text'),
             ('submitterPhone', '联系电话', 'text')],
         funcs='''
function openCreate() {
  openForm('登记投诉', fields, (m) => complaintApi.create(m))
}'''),

    dict(file='Visits', title='来访登记', tag='', api='visitApi', method='page',
         cols=[('visitNo', '来访号', 170), ('visitorName', '来访人', 120),
               ('personId', '被访人', 120), ('visitStatus', '状态', 110)],
         hint='来访可登记报告或转工单；无 approve 接口，动作是 report',
         bar='''      <el-button type="success" @click="openCreate">登记来访</el-button>''',
         rowbtns='''          <el-button link type="primary" @click="report(row)">登记报告</el-button>''',
         fields=[('visitType', '来访类型', 'text'), ('orgId', '组织ID', 'number'),
                 ('houseId', '房源ID', 'number')],
         funcs='''
function openCreate() {
  openForm('登记来访', fields, (m) => visitApi.create(m))
}
async function report(row) {
  await visitApi.report(row.id, {})
  ElMessage.success('已登记报告')
  load()
}'''),

    dict(file='ShortRent', title='短租订单', tag='民宿/网约房',
         api='shortRentApi', method='page',
         cols=[('orderNo', '订单号', 170), ('houseId', '房源', 120),
               ('checkInDate', '入住', 120), ('checkOutDate', '退房', 120),
               ('orderStatus', '状态', 110)],
         hint='入住区间左闭右开 [入住, 退房)，唯一索引防超卖；下单前需先看日房态',
         bar='', rowbtns='''
          <el-button link type="danger" @click="cancel(row)">取消</el-button>''',
         funcs='''
async function cancel(row) {
  const { value } = await ElMessageBox.prompt('请输入取消原因', '取消订单')
  await shortRentApi.cancel(row.id, value)
  ElMessage.success('已取消并释放房源')
  load()
}'''),

    dict(file='HouseCalendar', title='日房态', tag='', api='calendarApi',
         method='byHouse',
         cols=[('houseId', '房源', 120), ('calendarDate', '日期', 120),
               ('dayStatus', '日状态', 110), ('orderId', '占用订单', 150)],
         hint='日房态驱动短租可售判定。查询需房源ID（后端按 /house-calendar/{houseId}）',
         bar='''      <el-input v-model.number="houseId" placeholder="房源ID"
                style="width:150px" />
      <el-button type="primary" @click="reload">按房源查</el-button>''',
         rowbtns='', state='const houseId = ref(null)',
         param_extra=', houseId: houseId.value || undefined',
         funcs=''),

    dict(file='GovReport', title='监管报送', tag='对接房管局/公安',
         api='govApi', method='tasks',
         cols=[('taskNo', '任务号', 170), ('targetSystem', '目标系统', 150),
               ('reportType', '类型', 110), ('taskStatus', '状态', 110)],
         hint='适配器隔离 + 任务/明细双层，支持部分成功后精确补报',
         bar='''      <el-button type="success" @click="openCreate">发起报送</el-button>''',
         rowbtns='''          <el-button link type="warning" @click="retry(row)">补报</el-button>''',
         fields=[('targetSystem', '目标系统', 'select',
                  [('PUBLIC_HOUSING', '公租房系统'), ('POLICE', '公安'),
                   ('HOUSING', '住建'), ('REAL_ESTATE', '不动产')]),
                 ('reportType', '报送类型', 'select',
                  [('HOUSE', '房源'), ('TENANT', '租户'), ('CONTRACT', '合同')]),
                 ('dateFrom', '数据范围起', 'date'), ('dateTo', '数据范围止', 'date')],
         funcs='''
function openCreate() {
  openForm('发起监管报送', fields, (m) => govApi.submit(m),
    { targetSystem: 'PUBLIC_HOUSING', reportType: 'HOUSE' },
    '未配置适配器时任务会失败并提示，不会阻断业务')
}
async function retry(row) {
  const n = await govApi.retry(row.id)
  ElMessage.success(`补报完成：成功 ${n} 条`)
  load()
}'''),

    dict(file='OpenApps', title='开放平台', tag='第三方/政务接入',
         api='openApi', method='apps',
         cols=[('appKey', 'AppKey', 200), ('appName', '应用名', 150),
               ('appType', '类型', 120), ('appStatus', '状态', 100)],
         hint='AppSecret 仅创建时明文返回一次；密钥 AES-GCM 加密存储以支持签名复算',
         bar='''      <el-button type="success" @click="openCreate">创建应用</el-button>''',
         rowbtns='''          <el-button link type="warning" @click="resetSecret(row)">重置密钥</el-button>''',
         fields=[('appName', '应用名称', 'text'),
                 ('appType', '应用类型', 'select',
                  [('THIRD_PARTY', '第三方'), ('INTERNAL', '内部'), ('GOV', '政务')]),
                 ('ownerOrg', '所属单位', 'text'),
                 ('contactName', '联系人', 'text'),
                 ('contactPhone', '联系电话', 'text'),
                 ('ipWhitelist', 'IP白名单', 'text'),
                 ('qpsLimit', 'QPS限流', 'number'),
                 ('dailyQuota', '日调用配额', 'number'),
                 ('scopeCodes', '授权接口范围', 'text'),
                 ('expireDate', '有效期', 'date')],
         funcs='''
function openCreate() {
  openForm('创建开放应用', fields, (m) => openApi.createApp(m),
    { appType: 'THIRD_PARTY', qpsLimit: 20, scopeCodes: '*' },
    '创建成功后 AppSecret 只显示这一次，请立即保存')
}
async function resetSecret(row) {
  await ElMessageBox.confirm('重置后旧密钥立即失效，确认继续？', '提示',
    { type: 'warning' })
  const r = await openApi.resetSecret(row.id)
  ElMessageBox.alert(`新密钥（仅此一次）：\\n${r.appSecret}`, '请立即保存',
    { type: 'success' })
}'''),
]


def render_fields(fs):
    if not fs:
        return '[]'
    out = []
    for f in fs:
        if len(f) == 3:
            key, label, typ = f
            extra = ''
        else:
            key, label, typ, opts = f
            extra = ", options: [" + ', '.join(S(v, l) for v, l in opts) + ']'
        out.append("{ key: '%s', label: '%s', type: '%s'%s }" % (key, label, typ, extra))
    return '[\n  ' + ',\n  '.join(out) + '\n]'


n = 0
for c in CFG:
    col_src = '\n'.join('      <el-table-column prop="%s" label="%s" width="%d" />' % x
                        for x in c['cols'])
    content = (TPL
               .replace('{{TITLE}}', c['title'])
               .replace('{{TAG}}', c['tag'])
               .replace('{{API}}', c['api'])
               .replace('{{METHOD}}', c['method'])
               .replace('{{COLUMNS}}', col_src)
               .replace('{{HINT}}', c['hint'].replace("'", "\\'"))
               .replace('{{ACTIONS_BAR}}', c.get('bar', ''))
               .replace('{{ROWACTION_BTNS}}', c.get('rowbtns', ''))
               .replace('{{ROWACTIONS}}', 'true' if c.get('rowbtns') else '')
               .replace('{{FIELDS_JSON}}', render_fields(c.get('fields')))
               .replace('{{PARAM_EXTRA}}', c.get('param_extra', ''))
               .replace('{{STATE}}', c.get('state', ''))
               .replace('{{FUNCS}}', c.get('funcs', '')))
    io.open(os.path.join(BASE, c['file'] + '.vue'), 'w', encoding='utf-8').write(content)
    n += 1
    has_form = '✓ 表单' if c.get('fields') else '— 仅查询'
    print('  %-16s %-14s %s' % (c['file'] + '.vue', c['title'], has_form))

print()
print('重新生成 %d 个页面（其中 %d 个带写操作表单）'
      % (n, sum(1 for c in CFG if c.get('fields'))))
