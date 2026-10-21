# -*- coding: utf-8 -*-
"""为 6 个查询型页面补写操作：申诉/信用/换房/投诉/告警/钥匙包

设计：行内动作按钮（body 用 ReasonCmd/UserCmd 等简单结构）+ JSON 新建对话框
（避免凭猜测写字段；对话框给出后端真实字段示例，可编辑提交）
"""
import io
import os

V = r'D:\Work\业务平台开发\frontend\src\views'

TPL = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{TITLE}}</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
{{TOPBAR}}
    </div>

    <el-alert type="info" :closable="false" show-icon :title="HINT"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <pre class="raw">{{ JSON.stringify(row, null, 2) }}</pre>
        </template>
      </el-table-column>
{{COLS}}
      <el-table-column label="操作" width="{{OPW}}" fixed="right">
        <template #default="{ row }">
{{ACTIONS}}
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="createVisible" title="新建" width="560px">
      <el-alert type="warning" :closable="false" show-icon
                title="字段取自后端 Cmd 定义，可直接编辑；数字 ID 请填真实主键" />
      <el-input v-model="json" type="textarea" :rows="16"
                style="margin-top:10px;font-family:monospace" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <pre class="raw">{{ JSON.stringify(detail, null, 2) }}</pre>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
const createVisible = ref(false)
const json = ref(JSON.stringify({{SAMPLE}}, null, 2))

async function load() {
  loading.value = true
  try {
    const d = await req.get('{{LIST}}', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  let body
  try { body = JSON.parse(json.value) } catch (e) {
    ElMessage.error('JSON 格式错误'); return
  }
  saving.value = true
  try {
    await req.post('{{CREATE}}', body)
    ElMessage.success('创建成功')
    createVisible.value = false; load()
  } finally { saving.value = false }
}

/** 带原因的动作 */
async function actReason(row, path, label) {
  const { value } = await ElMessageBox.prompt('请输入' + label + '原因', label, {
    inputValue: ''
  })
  await req.post(`${pathTpl(path, row.id)}`, { reason: value })
  ElMessage.success(label + '成功'); load()
}
function pathTpl(p, id) { return p.replace('{id}', id) }

/** 无参数动作 */
async function actPlain(row, path, label) {
  await ElMessageBox.confirm('确认执行「' + label + '」？', label, { type: 'warning' })
  await req.post(pathTpl(path, row.id))
  ElMessage.success(label + '成功'); load()
}

{{FUNCS}}

onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
'''

CFG = [
    dict(file='Appeals', title='申诉管理', list='/appeals', create='/appeals',
         hint='申诉期限默认 10 个自然日（可配）；逾期未处理会标记超时',
         opw=250,
         sample={'applicantPersonId': 1, 'appealType': 'REVIEW_RESULT',
                 'appealReason': '对审核结论有异议', 'evidenceUrl': '',
                 'relatedBizId': 1},
         actions=[('accept', '受理', 'reason', '受理'),
                  ('investigate', '调查', 'reason', '调查'),
                  ('decide', '决定', 'reason', '决定'),
                  ('notify', '通知', 'plain', '通知'),
                  ('withdraw', '撤回', 'reason', '撤回')],
         topbar='      <el-button @click="markTimeout">标记超时</el-button>'),
    dict(file='Credits', title='信用惩戒', list='/credits', create='/credits',
         hint='失信限制再申请 5 年；到期可扫描自动失效',
         opw=250,
         sample={'personId': 1, 'creditType': 'RENT_ARREARS',
                 'creditLevel': 'MINOR', 'reason': '欠租超过 6 个月',
                 'startDate': '2026-01-01', 'endDate': '2031-01-01',
                 'banApplyFlag': 1},
         actions=[('revoke', '撤销', 'reason', '撤销'),
                  ('expire', '标记失效', 'reason', '失效'),
                  ('push', '推送', 'plain', '推送')],
         topbar='      <el-button @click="scanExpired">扫描到期</el-button>'),
    dict(file='Exchanges', title='换房管理', list='/exchanges', create='/exchanges',
         hint='成都限 1 次；重庆「应换不换」按 1.5 倍租金计收',
         opw=270,
         sample={'personId': 1, 'contractId': 1, 'fromHouseId': 1,
                 'toHouseId': 2, 'exchangeReason': '家庭人口增加',
                 'exchangeCount': 1},
         actions=[('submit', '提交', 'plain', '提交'),
                  ('approve', '批准', 'reason', '批准'),
                  ('reject', '驳回', 'reason', '驳回'),
                  ('complete', '完成', 'plain', '完成'),
                  ('no-exchange', '应换不换', 'reason', '登记')],
         topbar=''),
    dict(file='Complaints', title='投诉管理', list='/complaints',
         create='/complaints',
         hint='投诉可由住户/工作人员发起，需在时限内办结',
         opw=170,
         sample={'complainantPersonId': 1, 'complaintType': 'SERVICE',
                 'complaintContent': '报修长时间未处理', 'orgId': 1},
         actions=[('close', '办结', 'reason', '办结')],
         topbar=''),
    dict(file='Alerts', title='告警与规则', list='/alerts', create='/alerts',
         hint='阈值告警由规则引擎产生；可转工单、升级或忽略',
         opw=280,
         sample={'alertType': 'ARREAR_RATE', 'alertLevel': 'WARNING',
                 'alertContent': '欠费率达到 15%', 'orgId': 1},
         actions=[('handle', '处理', 'action', '处理'),
                  ('resolve', '解决', 'action', '解决'),
                  ('ignore', '忽略', 'action', '忽略'),
                  ('escalate', '升级', 'action', '升级'),
                  ('to-workorder', '转工单', 'action', '转工单')],
         topbar='      <el-button @click="loadStats">告警统计</el-button>'),
    dict(file='Keyring', title='钥匙包', list='/keyring', create='/keyring',
         hint='钥匙包绑定房源与房间号；状态变更与回收需留痕',
         opw=190,
         sample={'houseId': 1, 'keyringNo': 'KR001', 'keyCount': 2,
                 'holderPersonId': 1, 'keyringStatus': 'IN_USE'},
         actions=[('status', '改状态', 'plain', '改状态'),
                  ('remove', '回收', 'plain', '回收')],
         topbar=''),
]

COLS = {
    'Appeals': [('appealNo', '申诉单号', 170), ('appealType', '类型', 130),
                ('appealStatus', '状态', 110), ('applicantPersonId', '申请人', 120)],
    'Credits': [('personId', '人员', 120), ('creditType', '类型', 140),
                ('creditLevel', '级别', 100), ('creditStatus', '状态', 110),
                ('endDate', '截止', 110)],
    'Exchanges': [('exchangeNo', '换房单号', 170), ('personId', '人员', 110),
                  ('fromHouseId', '原房源', 120), ('toHouseId', '新源房', 120),
                  ('exchangeStatus', '状态', 110)],
    'Complaints': [('complaintNo', '投诉单号', 170), ('complaintType', '类型', 130),
                   ('complaintStatus', '状态', 110),
                   ('complainantPersonId', '投诉人', 120)],
    'Alerts': [('alertType', '告警类型', 150), ('alertLevel', '级别', 100),
               ('alertStatus', '状态', 110), ('alertContent', '内容', 200)],
    'Keyring': [('keyringNo', '编号', 140), ('houseId', '房源', 120),
                ('keyCount', '钥匙数', 100), ('keyringStatus', '状态', 110)],
}

n = 0
for c in CFG:
    col_src = '\n'.join('      <el-table-column prop="%s" label="%s" width="%d" />' % x
                        for x in COLS[c['file']])
    # 动作按钮
    acts = []
    funcs = []
    for path, label, kind, tag in c['actions']:
        if kind == 'reason':
            acts.append('          <el-button link type="primary" @click="actReason(row, '
                        "'/api/v1/%s/{id}/%s', '%s')\">%s</el-button>"
                        % (c['list'].strip('/'), path, tag, label))
        elif kind == 'plain':
            acts.append('          <el-button link @click="actPlain(row, '
                        "'/api/v1/%s/{id}/%s', '%s')\">%s</el-button>"
                        % (c['list'].strip('/'), path, tag, label))
        else:  # action: ActionCmd{handleUserId, action, result}
            acts.append('          <el-button link type="warning" @click="actAction(row, '
                        "'/api/v1/%s/{id}/%s', '%s')\">%s</el-button>"
                        % (c['list'].strip('/'), path, tag, label))
    if any(a[2] == 'action' for a in c['actions']):
        funcs.append('''async function actAction(row, path, label) {
  const { value } = await ElMessageBox.prompt('处理结果', label, { inputValue: '' })
  await req.post(pathTpl(path, row.id),
                 { handleUserId: 1, action: label, result: value })
  ElMessage.success(label + '成功'); load()
}''')
    if c['file'] == 'Appeals':
        funcs.append('''async function markTimeout() {
  const r = await req.post('/appeals/mark-timeout')
  ElMessage.success('已标记超时：' + (r?.count ?? '完成')); load()
}''')
    if c['file'] == 'Credits':
        funcs.append('''async function scanExpired() {
  const r = await req.post('/credits/scan-expired')
  ElMessage.success('扫描完成：' + (r?.count ?? '完成')); load()
}''')
    if c['file'] == 'Alerts':
        funcs.append('''async function loadStats() {
  const r = await req.get('/alerts/stats')
  ElMessageBox.alert(JSON.stringify(r, null, 2).slice(0, 900), '告警统计')
}''')

    src = (TPL.replace('{{TITLE}}', c['title'])
              .replace('{{HINT}}', c['hint'])
              .replace('{{TOPBAR}}', c['topbar'])
              .replace('{{COLS}}', col_src)
              .replace('{{OPW}}', str(c['opw']))
              .replace('{{ACTIONS}}', '\n'.join(acts))
              .replace('{{LIST}}', c['list'])
              .replace('{{CREATE}}', c['create'])
              .replace('{{SAMPLE}}', repr(c['sample']).replace("'", '"'))
              .replace('{{FUNCS}}', '\n'.join(funcs)))
    io.open(os.path.join(V, c['file'] + '.vue'), 'w', encoding='utf-8').write(src)
    n += 1
    print('  + %-12s %s（%d 个动作）' % (c['file'], c['title'], len(c['actions'])))
print('\n生成 %d 个可操作页面' % n)
