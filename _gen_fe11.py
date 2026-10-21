# -*- coding: utf-8 -*-
"""配置驱动生成剩余 14 个模块页面（共享模板，避免逐页手写）"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'

# ==================== 共享列表页模板 ====================
TPL = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{TITLE}}</h3>
      <el-tag v-if="TAG" size="small" type="info">{{TAG}}</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字/ID" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
{{EXTRA_FILTERS}}
    </div>

    <el-alert v-if="HINT" type="info" :closable="false" show-icon
              :title="HINT" style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <pre class="raw">{{ JSON.stringify(row, null, 2) }}</pre>
        </template>
      </el-table-column>
{{COLUMNS}}
      <el-table-column label="操作" :width="ACTIONS ? 190 : 110" fixed="right">
        <template #default="{ row }">
{{ACTIONS}}
          <el-button link @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-drawer v-model="detailVisible" title="明细（原始数据）" size="520px">
      <pre class="raw">{{ JSON.stringify(detail, null, 2) }}</pre>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { {{API}} } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const detailVisible = ref(false)
const detail = ref(null)
{{STATE}}

async function load() {
  loading.value = true
  try {
    const data = await {{API}}.{{METHOD}}({
      pageNum: pageNum.value, pageSize: pageSize.value,
      ...buildParams()
    })
    rows.value = data.rows || data || []
    total.value = Number(data.total || rows.value.length || 0)
  } catch (e) {
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function buildParams() {
  return { keyword: keyword.value || undefined{{PARAM_EXTRA}} }
}

function reload() { pageNum.value = 1; load() }

function openDetail(row) { detail.value = row; detailVisible.value = true }
{{FUNCS}}

onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
'''

# (文件名, 标题, 标签, API, 方法, 列定义[(prop,label,width)], 提示, 额外筛选器, 额外参数, 动作, 额外方法)
CONFIGS = [
    ('Persons', '保障对象', '人员档案', 'personApi', 'page',
     [('personName', '姓名', 120), ('idCardMask', '证件(脱敏)', 160),
      ('phone', '电话', 130), ('personStatus', '状态', 100)],
     '人员基础信息；保障专有属性在「保障档案」中维护',
     '', '', '', ''),

    ('Spaces', '空间层级', '小区→楼栋→单元→楼层→房→床', 'spaceApi', 'page',
     [('spaceName', '空间名称', 160), ('spaceType', '类型', 110),
      ('pathCode', '路径编码', 150), ('orgId', '组织', 130)],
     '层级：AREA/BUILDING/UNIT/FLOOR/ROOM/BED/PARKING；path_code 每级 2 位',
     '', '', '', ''),

    ('Terminations', '退租管理', '', 'terminationApi', 'page',
     [('terminationNo', '退租单号', 170), ('contractId', '合同', 130),
      ('terminationType', '类型', 120), ('terminationStatus', '状态', 110),
      ('planExitDate', '计划退出', 120)],
     '腾退会生成过渡期（月数与租金倍率由系统参数控制）',
     '', '', '', ''),

    ('Appeals', '申诉管理', '救济通道', 'appealApi', 'page',
     [('appealNo', '申诉号', 170), ('bizType', '业务类型', 130),
      ('appealStatus', '状态', 110), ('deadlineTime', '申诉期限', 170)],
     '申诉期限默认 10 天（可配）；异议成立会回写原业务',
     '', '', '', ''),

    ('Credits', '信用与惩戒', '', 'creditApi', 'page',
     [('personId', '人员', 120), ('violationType', '违规类型', 150),
      ('sanctionType', '惩戒措施', 150), ('banEndDate', '限制至', 120)],
     '严重违规默认限制申请 5 年、一般 1 年（均由系统参数控制）',
     '', '', '', ''),

    ('Exchanges', '同租期限换房', '', 'exchangeApi', 'page',
     [('exchangeNo', '换房单号', 170), ('oldContractId', '原合同', 130),
      ('newHouseId', '新房屋', 130), ('exchangeStatus', '状态', 110),
      ('rentMultiplier', '加价倍率', 110)],
     '同一租期限换 1 次；应换不换按 1.5 倍计租（可配）',
     '', '', '', ''),

    ('Complaints', '投诉工单', '', 'complaintApi', 'page',
     [('complaintNo', '投诉号', 170), ('complaintType', '类型', 130),
      ('complaintStatus', '状态', 110), ('createTime', '受理时间', 170)],
     '', '', '', '', ''),

    ('Visits', '来访登记', '', 'visitApi', 'page',
     [('visitNo', '来访号', 170), ('visitorName', '来访人', 120),
      ('personId', '被访人', 120), ('visitStatus', '状态', 110),
      ('planVisitTime', '预约时间', 170)],
     '', '', '', '', ''),

    ('ShortRent', '短租订单', '民宿/网约房', 'shortRentApi', 'page',
     [('orderNo', '订单号', 170), ('houseId', '房源', 120),
      ('checkInDate', '入住', 120), ('checkOutDate', '退房', 120),
      ('orderStatus', '状态', 110), ('totalAmount', '金额', 110)],
     '入住区间左闭右开 [入住, 退房)，唯一索引防超卖',
     '', '', '', ''),

    ('HouseCalendar', '日房态', '', 'calendarApi', 'page',
     [('houseId', '房源', 120), ('calendarDate', '日期', 120),
      ('dayStatus', '日状态', 110), ('orderId', '占用订单', 150)],
     '日房态表驱动短租可售判定，避免超卖',
     '', '', '', ''),

    ('GovReport', '监管报送', '对接房管局/公安', 'govApi', 'tasks',
     [('taskNo', '任务号', 170), ('targetSystem', '目标系统', 150),
      ('reportType', '类型', 110), ('recordCount', '记录数', 100),
      ('successCount', '成功', 90), ('taskStatus', '状态', 110)],
     '适配器隔离 + 任务/明细双层，支持部分成功精确补报',
     '', '', '', ''),

    ('OpenApps', '开放平台', '第三方/政务接入', 'openApi', 'apps',
     [('appKey', 'AppKey', 200), ('appName', '应用名', 150),
      ('appType', '类型', 120), ('qpsLimit', 'QPS', 90),
      ('expireDate', '有效期', 120), ('appStatus', '状态', 100)],
     'AppSecret 仅创建时明文返回一次；密钥用 AES-GCM 加密存储以支持签名复算',
     '', '', '', ''),
]

# ==================== 生成配置驱动页面 ====================
for (name, title, tag, api, method, cols, hint, extra_f, extra_p, actions,
     funcs) in CONFIGS:
    col_src = '\n'.join(
        '      <el-table-column prop="%s" label="%s" width="%d" />' % c
        for c in cols)
    content = (TPL
               .replace('{{TITLE}}', title)
               .replace('{{TAG}}', tag)
               .replace('{{API}}', api)
               .replace('{{METHOD}}', method)
               .replace('{{COLUMNS}}', col_src)
               .replace('{{HINT}}', hint.replace("'", "\\'"))
               .replace('{{EXTRA_FILTERS}}', extra_f)
               .replace('{{PARAM_EXTRA}}', extra_p)
               .replace('{{ACTIONS}}', actions)
               .replace('{{FUNCS}}', funcs)
               .replace('{{STATE}}', ''))
    p = os.path.join(BASE, 'src', 'views', name + '.vue')
    io.open(p, 'w', encoding='utf-8').write(content)
    print('  + views/%-16s %s' % (name + '.vue', title))

print('配置驱动页面 %d 个' % len(CONFIGS))
