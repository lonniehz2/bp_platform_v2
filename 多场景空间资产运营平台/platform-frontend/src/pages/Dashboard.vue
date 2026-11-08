<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const loading = ref(true)
const error = ref('')
const projects = ref([])
const applications = ref([])
const contracts = ref([])
const bills = ref([])
const devices = ref([])
const project = ref(null)

const count = (list, status, field = 'status') => list.filter(x => x[field] === status).length
const money = (value) => Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function load() {
  loading.value = true
  error.value = ''
  try {
    projects.value = await api.projects()
    const saved = String(localStorage.getItem('platformProjectId') || '')
    project.value = projects.value.find(p => String(p.id) === saved)
      || projects.value.slice().sort((a, b) =>
        ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
        ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
      )[0] || null
    if (project.value) {
      const id = project.value.id
      const [a, c, b, d] = await Promise.all([
        api.applications(id), api.contracts(id), api.bills(id), api.devices(id)
      ])
      applications.value = a
      contracts.value = c
      bills.value = b
      devices.value = d
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid cards">
      <div class="card">
        <div class="label">项目数</div>
        <div class="value">{{ projects.length }}</div>
        <div class="hint">当前租户全部项目</div>
      </div>
      <div class="card">
        <div class="label">保障房申请</div>
        <div class="value">{{ applications.length }}</div>
        <div class="hint">待审 {{ count(applications, 'SUBMITTED', 'applicationStatus') }}</div>
      </div>
      <div class="card">
        <div class="label">生效合同</div>
        <div class="value">{{ contracts.filter(c => c.contractStatus === 'ACTIVE').length }}</div>
        <div class="hint">合同总数 {{ contracts.length }}</div>
      </div>
      <div class="card">
        <div class="label">应收账单</div>
        <div class="value">{{ bills.length }}</div>
        <div class="hint">未结清 {{ bills.filter(b => b.billStatus !== 'PAID').length }}</div>
      </div>
      <div class="card">
        <div class="label">设备资产</div>
        <div class="value">{{ devices.length }}</div>
        <div class="hint">业务台账</div>
      </div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head">
        <div>
          <h2>当前项目</h2>
          <p>保障房第一个场景 · 申请到收款的闭环入口</p>
        </div>
        <span class="pill">{{ project?.orgCode || '未选择项目' }}</span>
      </div>
      <div v-if="loading" class="empty">加载中…</div>
      <div v-else-if="!project" class="empty">暂无项目，请先到“项目与资产”创建项目。</div>
      <div v-else class="row">
        <div class="field">
          <label>项目名称</label>
          <div>{{ project.orgName }}</div>
        </div>
        <div class="field">
          <label>经营模式</label>
          <div>{{ project.businessMode }}</div>
        </div>
        <div class="field">
          <label>空间模板</label>
          <div>{{ project.templateName || project.spaceTemplateId }}</div>
        </div>
        <div class="field">
          <label>状态</label>
          <div><span class="badge green">{{ project.status }}</span></div>
        </div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(340px, 1fr))">
      <div class="panel">
        <div class="panel-head"><h2>最近合同</h2><RouterLink to="/contracts">查看全部</RouterLink></div>
        <div v-if="!contracts.length" class="empty">暂无合同</div>
        <div v-for="c in contracts.slice(0, 5)" :key="c.id" class="row" style="border-bottom:1px solid var(--line);padding:9px 0">
          <div style="flex:1">
            <div>{{ c.contractNo }}</div>
            <div class="small muted">{{ c.personName }} · {{ c.houseName }}</div>
          </div>
          <span class="badge" :class="c.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ c.contractStatus }}</span>
          <span class="mono">¥{{ money(c.rentAmount) }}</span>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>待处理账单</h2><RouterLink to="/billing">去收款</RouterLink></div>
        <div v-if="!bills.length" class="empty">暂无账单</div>
        <div v-for="b in bills.filter(x => x.billStatus !== 'PAID').slice(0, 5)" :key="b.id" class="row" style="border-bottom:1px solid var(--line);padding:9px 0">
          <div style="flex:1">
            <div>{{ b.billNo }}</div>
            <div class="small muted">{{ b.periodStart }} ~ {{ b.periodEnd }}</div>
          </div>
          <span class="badge orange">{{ b.billStatus }}</span>
          <span class="mono">¥{{ money(b.payableAmount || b.amount) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
