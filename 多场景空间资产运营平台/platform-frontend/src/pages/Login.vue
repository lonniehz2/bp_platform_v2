<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const busy = ref(false)
const error = ref('')
const form = reactive({ username: 'admin', password: 'admin123', tenantId: '350600' })

async function submit() {
  busy.value = true
  error.value = ''
  try {
    const result = await api.login({
      username: form.username.trim(),
      password: form.password,
      tenantId: form.tenantId.trim()
    })
    localStorage.setItem('platformToken', result.token)
    localStorage.setItem('platformUser', JSON.stringify(result))
    const menus = await api.myMenus('GUARANTEE')
    localStorage.setItem('platformMenus', JSON.stringify(menus))
    await router.replace('/')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand" style="padding:0 0 18px">
        <div class="brand-mark">MS</div>
        <div>
          <div class="brand-title">多场景空间资产</div>
          <div class="brand-sub">运营平台 · 保障房场景</div>
        </div>
      </div>
      <h2 style="margin:0 0 4px">登录</h2>
      <p class="muted small" style="margin:0 0 18px">租户 350600 · GUARANTEE 场景</p>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="field" style="margin-bottom:10px">
        <label>租户</label>
        <input v-model="form.tenantId" />
      </div>
      <div class="field" style="margin-bottom:10px">
        <label>用户名</label>
        <input v-model="form.username" autocomplete="username" />
      </div>
      <div class="field" style="margin-bottom:16px">
        <label>密码</label>
        <input v-model="form.password" type="password" autocomplete="current-password" @keyup.enter="submit" />
      </div>
      <button class="primary" style="width:100%" :disabled="busy" @click="submit">{{ busy ? '登录中…' : '登录' }}</button>
      <p class="small muted" style="margin:14px 0 0">演示账号：admin / admin123</p>
    </div>
  </div>
</template>
