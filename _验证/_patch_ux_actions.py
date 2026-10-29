# -*- coding: utf-8 -*-
"""操作列收窄：次要动作进「更多▾」。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')


def patch(fn, old, new, label):
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    if old not in s:
        print('  !', fn, '未匹配:', label)
        return
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔', fn, label)


patch('WorkOrders.vue', '''      <el-table-column label="操作" width="420" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.orderStatus === 'PENDING'" link type="warning"
                     @click="autoAssign(row)" data-testid="wo-autoassign">自动派单</el-button>
          <el-button link type="primary" @click="act(row, 'accept')">接单</el-button>
          <el-button link type="primary" @click="act(row, 'start')">开始</el-button>
          <el-button link type="success" @click="finish(row)">完成</el-button>
          <el-button link type="success" @click="closeOrder(row)">关单</el-button>
          <el-button link type="danger" @click="cancelOrder(row)">取消</el-button>
          <el-button link type="warning" @click="rejectOrder(row)">退回</el-button>
          <el-button link @click="logs(row)">日志</el-button>
        </template>
      </el-table-column>''', '''      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.orderStatus === 'PENDING'" link type="warning"
                     @click="autoAssign(row)" data-testid="wo-autoassign">自动派单</el-button>
          <el-button link type="primary" @click="act(row, 'accept')">接单</el-button>
          <el-button link type="success" @click="finish(row)">完成</el-button>
          <el-dropdown trigger="click" style="margin-left:8px">
            <el-button link type="primary">更多▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="act(row, 'start')">开始</el-dropdown-item>
                <el-dropdown-item @click="closeOrder(row)">关单</el-dropdown-item>
                <el-dropdown-item @click="cancelOrder(row)">取消</el-dropdown-item>
                <el-dropdown-item @click="rejectOrder(row)">退回</el-dropdown-item>
                <el-dropdown-item @click="logs(row)">日志</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>''', '工单')

patch('Alerts.vue', '''      <el-table-column label="操作" width="424" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/handle', '处理')">处理</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/resolve', '解决')">解决</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/ignore', '忽略')">忽略</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/escalate', '升级')">升级</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/to-workorder', '转工单')">转工单</el-button>
        </template>
      </el-table-column>''', '''      <el-table-column label="操作" width="210" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/handle', '处理')">处理</el-button>
          <el-dropdown trigger="click" style="margin-left:8px">
            <el-button link type="primary">更多▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="actAction(row, '/api/v1/alerts/{id}/resolve', '解决')">解决</el-dropdown-item>
                <el-dropdown-item @click="actAction(row, '/api/v1/alerts/{id}/ignore', '忽略')">忽略</el-dropdown-item>
                <el-dropdown-item @click="actAction(row, '/api/v1/alerts/{id}/escalate', '升级')">升级</el-dropdown-item>
                <el-dropdown-item @click="actAction(row, '/api/v1/alerts/{id}/to-workorder', '转工单')">转工单</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>''', '告警')

patch('Appeals.vue', '''      <el-table-column label="操作" width="420" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/appeals/{id}/accept', '受理')">受理</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/appeals/{id}/investigate', '调查')">调查</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/appeals/{id}/decide', '决定')">决定</el-button>
          <el-button link @click="actPlain(row, '/api/v1/appeals/{id}/notify', '通知')">通知</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/appeals/{id}/withdraw', '撤回')">撤回</el-button>
        </template>
      </el-table-column>''', '''      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/appeals/{id}/accept', '受理')">受理</el-button>
          <el-dropdown trigger="click" style="margin-left:8px">
            <el-button link type="primary">更多▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="actReason(row, '/api/v1/appeals/{id}/investigate', '调查')">调查</el-dropdown-item>
                <el-dropdown-item @click="actReason(row, '/api/v1/appeals/{id}/decide', '决定')">决定</el-dropdown-item>
                <el-dropdown-item @click="actPlain(row, '/api/v1/appeals/{id}/notify', '通知')">通知</el-dropdown-item>
                <el-dropdown-item @click="actReason(row, '/api/v1/appeals/{id}/withdraw', '撤回')">撤回</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>''', '申诉')

patch('Exchanges.vue', '''      <el-table-column label="操作" width="424" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link @click="actPlain(row, '/api/v1/exchanges/{id}/submit', '提交')">提交</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/exchanges/{id}/approve', '批准')">批准</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/exchanges/{id}/reject', '驳回')">驳回</el-button>
          <el-button link @click="actPlain(row, '/api/v1/exchanges/{id}/complete', '完成')">完成</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/exchanges/{id}/no-exchange', '登记')">应换不换</el-button>
        </template>
      </el-table-column>''', '''      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link @click="actPlain(row, '/api/v1/exchanges/{id}/submit', '提交')">提交</el-button>
          <el-dropdown trigger="click" style="margin-left:8px">
            <el-button link type="primary">更多▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="actReason(row, '/api/v1/exchanges/{id}/approve', '批准')">批准</el-dropdown-item>
                <el-dropdown-item @click="actReason(row, '/api/v1/exchanges/{id}/reject', '驳回')">驳回</el-dropdown-item>
                <el-dropdown-item @click="actPlain(row, '/api/v1/exchanges/{id}/complete', '完成')">完成</el-dropdown-item>
                <el-dropdown-item @click="actReason(row, '/api/v1/exchanges/{id}/no-exchange', '登记')">应换不换</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>''', '换房')

patch('Bills.vue', '''        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
            <el-button link type="primary" @click="openAllocate(row)">核销</el-button>
            <el-button link type="warning" @click="openWaive(row)">减免</el-button>
            <el-button link type="danger" @click="cancelBill(row)">取消</el-button>
            <el-button link @click="dunning(row)">催缴</el-button>
          </template>
        </el-table-column>''', '''        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
            <el-button link type="primary" @click="openAllocate(row)">核销</el-button>
            <el-dropdown trigger="click" style="margin-left:8px">
              <el-button link type="primary">更多▾</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="openWaive(row)">减免</el-dropdown-item>
                  <el-dropdown-item @click="cancelBill(row)">取消</el-dropdown-item>
                  <el-dropdown-item @click="dunning(row)">催缴</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>''', '账单')
