<template>
  <div>
    <div class="hero" style="padding-bottom:28px">
      <div class="title">{{ auth.displayName }}</div>
      <div class="sub">{{ auth.user?.tenantId }} · {{ auth.user?.userType || t('h5.profileUser') }}</div>
    </div>

    <div class="card">
      <div class="row"><b>{{ t('h5.bindTarget') }}</b><div class="spacer" />
        <el-tag size="small" :type="bound ? 'success' : 'warning'">
          {{ bound ? t('h5.bound') : t('h5.unbound') }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">
        {{ t('h5.bindHint') }}
      </div>
      <div class="row" style="margin-top:10px">
        <el-input v-model="pid" :placeholder="t('h5.pidHint')" />
        <el-button type="primary" @click="bind">{{ t('h5.bind') }}</el-button>
      </div>
    </div>

    <div class="card">
      <div class="row"><b>{{ t('h5.verifyStatus') }}</b><div class="spacer" />
        <el-tag size="small" :type="verify.verified ? 'success' : 'danger'">
          {{ verify.verified ? t('h5.verified') : t('h5.unverified') }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">{{ verify.conclusion }}</div>
    </div>

    <div class="card">
      <div class="row"><b>{{ t('h5.profile') }}</b><div class="spacer" />
        <el-tag v-if="profile" size="small">{{ profile.profileStatus }}</el-tag>
      </div>
      <div v-if="profile" style="margin-top:8px">
        <div class="muted">{{ t('h5.incomeLevel', { level: profile.incomeLevel, n: profile.familySize }) }}</div>
        <div class="muted" style="margin-top:4px">
          {{ t('h5.qualifyExpire', { date: profile.qualifyExpire || '—' }) }}
        </div>
      </div>
      <div v-else class="empty">{{ t('h5.noProfile') }}</div>
    </div>

    <div class="card">
      <el-button style="width:100%" @click="logout">{{ t('h5.logout') }}</el-button>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
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
