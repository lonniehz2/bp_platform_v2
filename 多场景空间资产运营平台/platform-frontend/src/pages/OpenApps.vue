<script setup>
import { onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const apps = ref([])
const error = ref('')
const busy = ref(false)
const createdSecret = ref('')
const form = reactive({ appCode: '', appName: '', scopes: '' })

async function load() {
  error.value = ''
  try { apps.value = await api.openApps() } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''; createdSecret.value = ''
  try {
    if (!form.appCode.trim() || !form.appName.trim()) throw new Error(t('openApps.required'))
    const r = await api.createOpenApp({ appCode: form.appCode.trim(), appName: form.appName.trim(), scopes: form.scopes })
    createdSecret.value = r.appSecret
    form.appCode = ''; form.appName = ''; form.scopes = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function toggle(a) {
  busy.value = true; error.value = ''
  try { await api.toggleOpenApp(a.id, a.appStatus !== 'ENABLED'); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('openApps.title') }}</h2><p>{{ t('openApps.subtitle') }}</p></div><span class="badge blue">{{ apps.length }} {{ t('openApps.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('openApps.appCode') }}</label><input v-model="form.appCode" :placeholder="t('openApps.codePlaceholder')" /></div>
        <div class="field"><label>{{ t('openApps.appName') }}</label><input v-model="form.appName" :placeholder="t('openApps.namePlaceholder')" /></div>
        <div class="field" style="flex:2"><label>{{ t('openApps.scopes') }}</label><input v-model="form.scopes" :placeholder="t('openApps.scopes')" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('open')" class="primary" :disabled="busy" @click="create">{{ t('openApps.create') }}</button></div>
      </div>
      <div v-if="createdSecret" class="alert" style="margin-top:10px">
        {{ t('openApps.secret') }}: <span class="mono">{{ createdSecret }}</span>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('openApps.list') }}</h2><span class="small muted">{{ t('openApps.hint') }}</span></div>
      <div v-if="!apps.length" class="empty">{{ t('openApps.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('openApps.appCode') }}</th><th>{{ t('openApps.name') }}</th><th>{{ t('openApps.scopes') }}</th><th>{{ t('openApps.status') }}</th><th>{{ t('openApps.createTime') }}</th><th>{{ t('openApps.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="a in apps" :key="a.id">
              <td class="mono">{{ a.appCode }}</td><td>{{ a.appName }}</td><td class="small">{{ a.scopes || '-' }}</td>
              <td><span class="badge" :class="a.appStatus === 'ENABLED' ? 'green' : 'orange'">{{ enumLabel(a.appStatus) }}</span></td>
              <td class="small">{{ a.createTime }}</td>
              <td><button v-if="can('open')" class="sm" @click="toggle(a)">{{ a.appStatus === 'ENABLED' ? t('openApps.disable') : t('openApps.enable') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
