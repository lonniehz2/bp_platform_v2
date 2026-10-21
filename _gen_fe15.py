# -*- coding: utf-8 -*-
"""补齐 console 有、SPA 缺的 8 个模块页面 + 路由"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend\src\views'

TPL = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{TITLE}}</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:170px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
{{BAR}}
    </div>
    <el-alert v-if="HINT" type="info" :closable="false" show-icon :title="HINT"
              style="margin-bottom:12px" />
    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><pre class="raw">{{ '{{' }} JSON.stringify(row, null, 2) {{ '}}' }}</pre></template>
      </el-table-column>
{{COLS}}
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />
    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <pre class="raw">{{ '{{' }} JSON.stringify(detail, null, 2) {{ '}}' }}</pre>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { {{API}} } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
{{STATE}}

async function load() {
  loading.value = true
  try {
    const data = await {{API}}.{{METHOD}}({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined{{PARAM}}
    })
    rows.value = data.rows || data || []
    total.value = Number(data.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }
onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
'''

CFG = [
    ('Subsidies', '补贴管理', 'subsidyApi', 'records',
     [('recordNo', '补贴单号', 170), ('personId', '人员', 120),
      ('subsidyMode', '补贴方式', 120), ('subsidyAmount', '金额', 110),
      ('recordStatus', '状态', 110)],
     '4 种补贴方式 + 月度封顶 + 抵扣租金联动；标准可按保障类型配置', '', ''),
    ('Deposits', '押金与退款', 'financeApi', 'deposits',
     [('contractId', '合同', 130), ('personId', '人员', 120),
      ('depositAmount', '应收押金', 120), ('paidAmount', '已收', 110),
      ('balanceAmount', '余额', 110), ('depositStatus', '状态', 110)],
     '余额 = 已收 − 已抵扣 − 已退还；抵扣 300 + 退还 1700 后状态应为 REFUNDED', '', ''),
    ('Publicities', '公示管理', 'publicityApi', 'page',
     [('publicityNo', '公示号', 170), ('publicityType', '类型', 130),
      ('title', '标题', 200), ('startDate', '开始', 110),
      ('endDate', '结束', 110), ('publicityStatus', '状态', 110)],
     '配租公示必须 ≥7 自然日且已结束才能签约（硬校验）', '', ''),
    ('Waitlist', '轮候管理', 'waitlistApi', 'page',
     [('personId', '人员', 120), ('totalScore', '总分', 100),
      ('waitDays', '轮候天数', 110), ('queueStatus', '状态', 110),
      ('enterTime', '入队时间', 170)],
     '总分 = 优先附加分 + 轮候天数 × 0.1；摇号按总分降序 → 入队升序', '', ''),
    ('FeeItems', '计费项目', 'financeApi', 'feeItems',
     [('itemCode', '项目编码', 150), ('itemName', '名称', 160),
      ('calcMode', '计费方式', 130), ('unitPrice', '单价', 100),
      ('status', '状态', 100)],
     '7 种计费方式：FIXED/BY_AREA/BY_HOUSE/BY_PERSON/BY_BED/BY_NIGHT/METER', '', ''),
    ('Arrears', '催缴管理', 'financeApi', 'arrears',
     [('billId', '账单', 130), ('personId', '人员', 120),
      ('actionType', '催缴方式', 130), ('actionTime', '时间', 170)],
     '催缴后仍不缴可触发欠费停权（默认不停大门）', '', ''),
    ('Cashflow', '资金流水', 'financeApi', 'cashflow',
     [('flowNo', '流水号', 170), ('bizType', '业务类型', 130),
      ('flowType', '收支', 100), ('amount', '金额', 110),
      ('flowTime', '时间', 170)],
     '核销/退款/补贴都会自动记账，形成完整资金流水', '', ''),
    ('ContractChanges', '合同变更', 'contractChangeApi', 'page',
     [('changeNo', '变更号', 170), ('contractId', '合同', 130),
      ('changeType', '变更类型', 130), ('changeStatus', '状态', 110)],
     '调租/租期/承租人变更，批准后写回合同', '', ''),
]

n = 0
for (file, title, api, method, cols, hint, bar, state) in CFG:
    col_src = '\n'.join('      <el-table-column prop="%s" label="%s" width="%d" />' % c
                        for c in cols)
    src = (TPL.replace('{{TITLE}}', title)
              .replace('{{API}}', api)
              .replace('{{METHOD}}', method)
              .replace('{{COLS}}', col_src)
              .replace('{{HINT}}', hint.replace("'", "\\'"))
              .replace('{{BAR}}', bar)
              .replace('{{STATE}}', state)
              .replace('{{PARAM}}', ''))
    # mustache 修正（模板里的转义写法还原）
    src = src.replace("{{ '{{' }} JSON.stringify(row, null, 2) {{ '}}' }}",
                      '{{ JSON.stringify(row, null, 2) }}')
    src = src.replace("{{ '{{' }} JSON.stringify(detail, null, 2) {{ '}}' }}",
                      '{{ JSON.stringify(detail, null, 2) }}')
    io.open(os.path.join(BASE, file + '.vue'), 'w', encoding='utf-8').write(src)
    n += 1
    print('  + %s.vue  %s' % (file, title))
print('生成 %d 个页面' % n)
