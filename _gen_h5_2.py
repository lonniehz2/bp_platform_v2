# -*- coding: utf-8 -*-
"""生成 H5 租客端页面"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

F['src/h5/views/H5Login.vue'] = '''<template>
  <div class="login">
    <div class="logo">住房保障</div>
    <div class="slogan">租客服务 · 掌上办理</div>

    <div class="form card">
      <el-form :model="form">
        <el-form-item>
          <el-input v-model="form.tenantId" placeholder="租户ID" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.username" placeholder="账号" size="large" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" show-password
                    placeholder="密码" size="large" />
        </el-form-item>
        <el-button type="primary" size="large" style="width:100%"
                   :loading="loading" @click="onLogin">登 录</el-button>
      </el-form>
      <div class="muted" style="margin-top:14px;text-align:center">
        演示账号 admin / admin123（租户 350600）
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ tenantId: '350600', username: 'admin', password: 'admin123' })

async function onLogin() {
  loading.value = true
  try {
    await auth.login({ ...form })
    ElMessage.success('登录成功')
    router.replace('/h5/home')
  } catch (e) { /* 已提示 */ } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  background: linear-gradient(160deg, #1f6feb 0%, #3f8cff 45%, #f2f4f7 45%);
  padding-top: 60px;
}
.logo { color: #fff; font-size: 26px; font-weight: 700; text-align: center; }
.slogan { color: rgba(255,255,255,.86); text-align: center; font-size: 13px; margin-top: 6px; }
.form { margin: 26px 20px; padding: 20px 16px; }
</style>
'''

F['src/h5/views/H5Home.vue'] = '''<template>
  <div>
    <div class="hero">
      <div class="title">{{ greeting }}，{{ auth.displayName }}</div>
      <div class="sub">{{ bound ? '已绑定保障对象 ID：' + personId : '尚未绑定保障对象，请到「我的」中绑定' }}</div>
    </div>

    <div class="card">
      <div class="grid4">
        <div class="item" @click="$router.push('/h5/bills')">
          <div class="icon"><el-icon><Money /></el-icon></div>
          <div class="label">我的账单</div>
        </div>
        <div class="item" @click="$router.push('/h5/applications')">
          <div class="icon"><el-icon><Document /></el-icon></div>
          <div class="label">申请进度</div>
        </div>
        <div class="item" @click="$router.push('/h5/access')">
          <div class="icon"><el-icon><Position /></el-icon></div>
          <div class="label">开门记录</div>
        </div>
        <div class="item" @click="$router.push('/h5/repairs')">
          <div class="icon"><el-icon><Tools /></el-icon></div>
          <div class="label">我要报修</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="row">
        <b>待缴金额</b>
        <div class="spacer" />
        <span v-if="loading" class="muted">加载中…</span>
      </div>
      <div class="amount" style="margin-top:8px">¥ {{ totalUnpaid }}</div>
      <div class="muted">共 {{ unpaidCount }} 张未缴账单</div>
    </div>

    <div class="card">
      <div class="row"><b>我的合同</b><div class="spacer" />
        <span class="muted">{{ contract ? contract.contractStatusLabel : '无' }}</span>
      </div>
      <div v-if="contract" style="margin-top:10px">
        <div>{{ contract.houseAddress }}</div>
        <div class="muted" style="margin-top:4px">
          {{ contract.contractNo }} · {{ contract.leaseStart }} ~ {{ contract.leaseEnd }}
        </div>
        <div class="muted" style="margin-top:4px">
          月租金 ¥{{ contract.monthlyRent }}
          <span v-if="Number(contract.daysToExpire) <= 30" style="color:#ff7d00">
            · 距到期 {{ contract.daysToExpire }} 天
          </span>
        </div>
      </div>
      <div v-else class="empty">暂无生效合同</div>
    </div>

    <div class="card">
      <div class="row"><b>我的待办</b><div class="spacer" />
        <span class="muted">{{ todos.length }} 条</span></div>
      <div v-for="t in todos.slice(0, 3)" :key="t.id" class="list-item">
        <div>{{ t.title }}</div>
        <div class="muted">{{ t.content }}</div>
      </div>
      <div v-if="!todos.length" class="empty">暂无待办</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { financeApi, contractApi, msgApi } from '@/api/modules'

const auth = useAuthStore()
const loading = ref(false)
const bills = ref([])
const contract = ref(null)
const todos = ref([])

const personId = computed(() => localStorage.getItem('bp_person_id') || '')
const bound = computed(() => !!personId.value)
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 11 ? '早上好' : h < 14 ? '中午好' : h < 18 ? '下午好' : '晚上好'
})
const unpaid = computed(() => bills.value.filter(
  (b) => ['UNPAID', 'PARTIAL', 'OVERDUE'].includes(b.billStatus)))
const unpaidCount = computed(() => unpaid.value.length)
const totalUnpaid = computed(() =>
  unpaid.value.reduce((s, b) => s + Number(b.payableAmount || 0), 0).toFixed(2))

async function load() {
  loading.value = true
  try {
    const pid = personId.value
    const b = await financeApi.bills({ pageNum: 1, pageSize: 50, personId: pid || undefined })
    bills.value = b.rows || []
    const c = await contractApi.page({ pageNum: 1, pageSize: 10 })
    contract.value = (c.rows || [])[0] || null
    if (auth.user?.userId) {
      const t = await msgApi.todos({ pageNum: 1, pageSize: 10, userId: auth.user.userId })
      todos.value = t.rows || []
    }
  } catch (e) { /* 已提示 */ } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
'''

F['src/h5/views/H5Bills.vue'] = '''<template>
  <div>
    <div class="navbar">我的账单</div>
    <div class="card">
      <div class="row"><b>待缴合计</b><div class="spacer" />
        <span class="amount" style="font-size:18px">¥ {{ totalUnpaid }}</span></div>
    </div>

    <div v-for="b in rows" :key="b.id" class="card">
      <div class="row">
        <b>{{ b.billPeriod }} 账单</b>
        <div class="spacer" />
        <el-tag size="small" :type="b.billStatus === 'PAID' ? 'success'
          : (b.overdueNow ? 'danger' : 'warning')">
          {{ b.billStatusLabel || b.billStatus }}
        </el-tag>
      </div>
      <div class="row" style="margin-top:8px">
        <span class="muted">{{ b.billNo }}</span>
        <div class="spacer" />
        <span class="amount" :class="{ ok: b.billStatus === 'PAID' }">
          ¥ {{ b.payableAmount }}
        </span>
      </div>
      <div class="muted" style="margin-top:6px">
        应收 ¥{{ b.billAmount }} · 已缴 ¥{{ b.paidAmount }} · 截止 {{ b.dueDate }}
        <span v-if="b.overdueDays > 0" style="color:#f53f3f"> · 逾期 {{ b.overdueDays }} 天</span>
      </div>
    </div>

    <div v-if="!rows.length" class="empty">暂无账单</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { financeApi } from '@/api/modules'

const rows = ref([])
const personId = localStorage.getItem('bp_person_id') || ''

const totalUnpaid = computed(() => rows.value
  .filter((b) => ['UNPAID', 'PARTIAL', 'OVERDUE'].includes(b.billStatus))
  .reduce((s, b) => s + Number(b.payableAmount || 0), 0).toFixed(2))

onMounted(async () => {
  const data = await financeApi.bills({
    pageNum: 1, pageSize: 50, personId: personId || undefined
  })
  rows.value = data.rows || []
})
</script>
'''

F['src/h5/views/H5Applications.vue'] = '''<template>
  <div>
    <div class="navbar">申请进度</div>

    <el-steps v-if="current" :active="stepOf(current)" simple style="margin:12px">
      <el-step title="提交" />
      <el-step title="受理" />
      <el-step title="审核" />
      <el-step title="结果" />
    </el-steps>

    <div v-for="a in rows" :key="a.id" class="card">
      <div class="row">
        <b>{{ a.applicationNo }}</b>
        <div class="spacer" />
        <el-tag size="small" :type="tagOf(a.applicationStatus)">
          {{ a.applicationStatusLabel || a.applicationStatus }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">
        {{ a.securityType }} · 家庭 {{ a.familySize }} 人 · 人均收入 ¥{{ a.incomePerCapita }}
      </div>
      <div class="muted" style="margin-top:4px">当前环节：{{ a.currentNode || '-' }}</div>
      <div v-if="a.rejectReason" style="margin-top:6px;color:#f53f3f;font-size:12px">
        不通过原因：{{ a.rejectReason }}
      </div>
      <div v-if="a.supplementDemand" style="margin-top:6px;color:#ff7d00;font-size:12px">
        需补件：{{ a.supplementDemand }}
      </div>
      <div class="muted" style="margin-top:6px">申请时间 {{ a.applyTime }}</div>
    </div>

    <div v-if="!rows.length" class="empty">暂无申请记录</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { applicationApi } from '@/api/modules'

const rows = ref([])
const personId = localStorage.getItem('bp_person_id') || ''
const current = computed(() => rows.value[0])

function stepOf(a) {
  const s = a.applicationStatus
  if (['APPROVED', 'REJECTED'].includes(s)) return 4
  if (['REVIEWING', 'SUPPLEMENT'].includes(s)) return 3
  if (s === 'ACCEPTED') return 2
  return 1
}
function tagOf(s) {
  return ({ APPROVED: 'success', REJECTED: 'danger',
    SUPPLEMENT: 'warning' })[s] || 'info'
}

onMounted(async () => {
  const data = await applicationApi.page({
    pageNum: 1, pageSize: 20, personId: personId || undefined
  })
  rows.value = data.rows || []
})
</script>
'''

F['src/h5/views/H5Access.vue'] = '''<template>
  <div>
    <div class="navbar"><span class="back" @click="$router.back()">←</span>我的开门记录</div>

    <div class="card">
      <div class="row"><b>不可信开门占比</b><div class="spacer" />
        <el-tag size="small" :type="ratio.pass ? 'success' : 'danger'">
          {{ ratio.pass ? '达标' : '超标' }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">
        {{ ratio.untrusted }} / {{ ratio.total }} 次 · 占比 {{ ratio.untrustedRatio }}%
        （阈值 {{ ratio.threshold }}%）
      </div>
    </div>

    <div v-for="r in rows" :key="r.id" class="card">
      <div class="row">
        <b>{{ r.openTypeName }}</b>
        <div class="spacer" />
        <el-tag v-if="r.abnormal" type="danger" size="small">异常</el-tag>
        <el-tag v-else-if="!r.trusted" type="warning" size="small">不可信</el-tag>
      </div>
      <div class="muted" style="margin-top:6px">{{ r.openTime }} · 门锁 {{ r.lockId }}</div>
    </div>

    <div v-if="!rows.length" class="empty">暂无开门记录</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { devApi } from '@/api/modules'

const rows = ref([])
const ratio = ref({})
const personId = localStorage.getItem('bp_person_id') || ''

onMounted(async () => {
  const data = await devApi.accessRecords({
    pageNum: 1, pageSize: 50, personId: personId || undefined
  })
  rows.value = data.rows || []
  ratio.value = await devApi.untrustedRatio()
})
</script>
'''

F['src/h5/views/H5Repairs.vue'] = '''<template>
  <div>
    <div class="navbar"><span class="back" @click="$router.back()">←</span>我要报修</div>

    <div class="card">
      <el-form :model="form" label-position="top">
        <el-form-item label="问题类型">
          <el-select v-model="form.type" style="width:100%">
            <el-option label="水电" value="WATER_ELECTRIC" />
            <el-option label="门窗" value="DOOR_WINDOW" />
            <el-option label="墙面渗漏" value="LEAK" />
            <el-option label="家电" value="APPLIANCE" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input v-model="form.description" type="textarea" :rows="4"
                    placeholder="请描述具体情况，便于师傅带工具上门" />
        </el-form-item>
        <el-form-item label="紧急程度">
          <el-radio-group v-model="form.urgency">
            <el-radio value="NORMAL">一般</el-radio>
            <el-radio value="URGENT">紧急</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-button type="primary" style="width:100%" :loading="saving"
                   @click="submit">提交报修</el-button>
      </el-form>
    </div>

    <div class="card">
      <b>提交说明</b>
      <div class="muted" style="margin-top:8px;line-height:1.7">
        · 报修会生成工单，并带 SLA 响应时限<br />
        · 紧急工单会同时通知值班人员<br />
        · 可在「我的」→ 待办 中查看处理进度
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'

const saving = ref(false)
const form = reactive({ type: 'WATER_ELECTRIC', description: '', urgency: 'NORMAL' })

async function submit() {
  if (!form.description) {
    ElMessage.warning('请填写问题描述')
    return
  }
  saving.value = true
  try {
    await req.post('/work-orders', {
      orderType: 'REPAIR',
      source: 'TENANT_APP',
      title: `住户报修：${form.type}`,
      description: form.description,
      priority: form.urgency,
      personId: localStorage.getItem('bp_person_id') || undefined
    })
    ElMessage.success('报修已提交')
    form.description = ''
  } catch (e) { /* 已提示 */ } finally {
    saving.value = false
  }
}
</script>
'''

F['src/h5/views/H5Profile.vue'] = '''<template>
  <div>
    <div class="hero" style="padding-bottom:28px">
      <div class="title">{{ auth.displayName }}</div>
      <div class="sub">{{ auth.user?.tenantId }} · {{ auth.user?.userType || '用户' }}</div>
    </div>

    <div class="card">
      <div class="row"><b>绑定保障对象</b><div class="spacer" />
        <el-tag size="small" :type="bound ? 'success' : 'warning'">
          {{ bound ? '已绑定' : '未绑定' }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">
        绑定后可查看本人账单、合同、申请与开门记录
      </div>
      <div class="row" style="margin-top:10px">
        <el-input v-model="pid" placeholder="请输入保障对象 ID" />
        <el-button type="primary" @click="bind">绑定</el-button>
      </div>
    </div>

    <div class="card">
      <div class="row"><b>实名认证状态</b><div class="spacer" />
        <el-tag size="small" :type="verify.verified ? 'success' : 'danger'">
          {{ verify.verified ? '已通过' : '未通过' }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">{{ verify.conclusion }}</div>
    </div>

    <div class="card">
      <div class="row"><b>保障档案</b><div class="spacer" />
        <el-tag v-if="profile" size="small">{{ profile.profileStatus }}</el-tag>
      </div>
      <div v-if="profile" style="margin-top:8px">
        <div class="muted">收入档位：{{ profile.incomeLevel }} · 家庭 {{ profile.familySize }} 人</div>
        <div class="muted" style="margin-top:4px">
          资格有效期至：{{ profile.qualifyExpire || '—' }}
        </div>
      </div>
      <div v-else class="empty">无档案或未绑定</div>
    </div>

    <div class="card">
      <el-button style="width:100%" @click="logout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import req from '@/api/request'

const auth = useAuthStore()
const router = useRouter()
const pid = ref(localStorage.getItem('bp_person_id') || '')
const verified = ref({})
const profile = ref(null)

const bound = computed(() => !!localStorage.getItem('bp_person_id'))
const verify = computed(() => verified.value || {})

async function load() {
  const id = localStorage.getItem('bp_person_id')
  if (!id) return
  try {
    verified.value = await req.get(`/verify-records/person/${id}/conclusion`)
  } catch (e) { /* 无记录 */ }
  try {
    profile.value = await req.get(`/guarantee-profiles/person/${id}`)
  } catch (e) { /* 无档案 */ }
}

function bind() {
  if (!pid.value) { ElMessage.warning('请输入保障对象 ID'); return }
  localStorage.setItem('bp_person_id', pid.value)
  ElMessage.success('已绑定')
  load()
}

function logout() {
  auth.logout()
  router.replace('/h5/login')
}

onMounted(load)
</script>
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个 H5 页面' % count)
