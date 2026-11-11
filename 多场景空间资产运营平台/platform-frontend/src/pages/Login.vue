<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '../api'
import { setLocale } from '../i18n'
import { mode, toggleMode } from '../ui'

const router = useRouter()
const { t, locale } = useI18n()
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
    try {
      const menus = await api.myMenus('GUARANTEE')
      localStorage.setItem('platformMenus', JSON.stringify(menus))
    } catch {}
    try {
      const actions = await api.myPermissions()
      localStorage.setItem('platformPermissions', JSON.stringify(actions))
    } catch {}
    const roles = result.roles || []
    const defaultPath = roles.some(r => ['GUARANTEE_ADMIN','GUARANTEE_MANAGER','ADMIN'].includes(r)) ? '/guarantee/cockpit' : '/guarantee/workbench'
    await router.replace(defaultPath)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function switchLocale() {
  setLocale(locale.value === 'zh-CN' ? 'en-US' : 'zh-CN')
}
</script>

<template>
  <div class="login-page">
    <div class="login-controls">
      <button class="ghost sm" @click="switchLocale">{{ locale === 'zh-CN' ? 'EN' : '中' }}</button>
      <button class="ghost sm" @click="toggleMode">{{ mode === 'dark' ? '☀' : '☾' }}</button>
    </div>

    <div class="login-shell">
      <section class="login-brand">
        <div class="brand-head">
          <div class="brand-mark">MS</div>
          <div>
            <h1>{{ t('login.brand') }}</h1>
            <p class="en">{{ t('login.en') }}</p>
          </div>
        </div>
        <p class="slogan">{{ t('login.slogan') }}</p>
        <ul class="features">
          <li><span class="dot" /><div><b>{{ t('login.flow') }}</b><em>{{ t('login.flowDesc') }}</em></div></li>
          <li><span class="dot" /><div><b>{{ t('login.assetTitle') }}</b><em>{{ t('login.assetDesc') }}</em></div></li>
          <li><span class="dot" /><div><b>{{ t('login.grantTitle') }}</b><em>{{ t('login.grantDesc') }}</em></div></li>
          <li><span class="dot" /><div><b>{{ t('login.multiTitle') }}</b><em>{{ t('login.multiDesc') }}</em></div></li>
        </ul>
        <div class="login-stats">
          <div><b>13</b><span>Pages</span></div>
          <div><b>6</b><span>Scenes</span></div>
          <div><b>24h</b><span>Online</span></div>
        </div>
      </section>

      <section class="login-card">
        <div class="card-head">
          <h2>{{ t('login.welcome') }}</h2>
          <p>{{ t('login.subtitle') }}</p>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
        <div class="field">
          <label>{{ t('login.tenant') }}</label>
          <input v-model="form.tenantId" autocomplete="organization" />
        </div>
        <div class="field">
          <label>{{ t('login.username') }}</label>
          <input v-model="form.username" autocomplete="username" />
        </div>
        <div class="field">
          <label>{{ t('login.password') }}</label>
          <input v-model="form.password" type="password" autocomplete="current-password" @keyup.enter="submit" />
        </div>
        <button class="primary login-submit" :disabled="busy" @click="submit">
          {{ busy ? '...' : t('login.submit') }}
        </button>
        <div class="login-hint">
          <div class="small muted">{{ t('login.demo') }}</div>
          <div class="row" style="margin-top:6px">
            <span class="badge blue">admin / admin123</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
