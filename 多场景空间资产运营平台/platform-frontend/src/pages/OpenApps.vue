<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

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
    if (!form.appCode.trim() || !form.appName.trim()) throw new Error('请填写应用编码和名称')
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
      <div class="panel-head"><div><h2>开放平台</h2><p>第三方应用接入凭证和授权范围</p></div><span class="badge blue">{{ apps.length }} 个应用</span></div>
      <div class="row">
        <div class="field"><label>应用编码</label><input v-model="form.appCode" placeholder="如 GOV_SYNC" /></div>
        <div class="field"><label>应用名称</label><input v-model="form.appName" placeholder="监管数据同步" /></div>
        <div class="field" style="flex:2"><label>授权范围</label><input v-model="form.scopes" placeholder="project:read,bill:read" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('open')" class="primary" :disabled="busy" @click="create">创建应用</button></div>
      </div>
      <div v-if="createdSecret" class="alert" style="margin-top:10px">
        应用密钥只显示一次：<span class="mono">{{ createdSecret }}</span>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>应用列表</h2><span class="small muted">停用后不可调用开放接口</span></div>
      <div v-if="!apps.length" class="empty">暂无应用</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>应用编码</th><th>名称</th><th>授权范围</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="a in apps" :key="a.id">
              <td class="mono">{{ a.appCode }}</td><td>{{ a.appName }}</td><td class="small">{{ a.scopes || '-' }}</td>
              <td><span class="badge" :class="a.appStatus === 'ENABLED' ? 'green' : 'orange'">{{ a.appStatus }}</span></td>
              <td class="small">{{ a.createTime }}</td>
              <td><button v-if="can('open')" class="sm" @click="toggle(a)">{{ a.appStatus === 'ENABLED' ? '停用' : '启用' }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
