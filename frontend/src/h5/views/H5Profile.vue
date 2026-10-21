<template>
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
