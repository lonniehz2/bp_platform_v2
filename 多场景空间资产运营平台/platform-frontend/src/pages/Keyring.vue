<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { confirmAction } from '../confirm'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const persons = ref([])
const personId = ref('')
const entries = ref([])
const error = ref('')
const busy = ref(false)

async function load() {
  error.value = ''
  try {
    persons.value = await api.persons()
    if (!personId.value && persons.value.length) personId.value = persons.value[0].id
    await loadKeyring()
  } catch (e) { error.value = e.message }
}

async function loadKeyring() {
  if (!personId.value) { entries.value = []; return }
  try { entries.value = await api.keyring(personId.value) } catch { entries.value = [] }
}

async function revoke(g) {
  if (!await confirmAction({ title: t('keyring.revokeTitle'), message: t('keyring.revokeMessage'), confirmText: t('keyring.revokeConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.revokeGrant(g.id, t('keyring.revokeReason')); await loadKeyring() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('keyring.title') }}</h2><p>{{ t('keyring.subtitle') }}</p></div><span class="badge blue">{{ entries.length }} {{ t('keyring.count') }}</span></div>
      <div class="field" style="max-width:320px"><label>{{ t('keyring.person') }}</label><SearchSelect v-model="personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('keyring.search')" @change="loadKeyring" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('keyring.list') }}</h2><span class="small muted">{{ t('keyring.hint') }}</span></div>
      <div v-if="!entries.length" class="empty">{{ t('keyring.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('keyring.target') }}</th><th>{{ t('keyring.type') }}</th><th>{{ t('keyring.level') }}</th><th>{{ t('keyring.validity') }}</th><th>{{ t('keyring.status') }}</th><th>{{ t('keyring.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="g in entries" :key="g.id">
              <td>{{ g.targetName || g.targetId }}</td><td>{{ g.targetType }}</td><td>{{ g.grantLevel }}</td>
              <td class="small">{{ g.validStart }} ~ {{ g.validEnd || t('keyring.longTerm') }}</td>
              <td><span class="badge green">{{ g.grantStatus }}</span></td>
              <td><button class="sm danger" :disabled="busy" @click="revoke(g)">{{ t('keyring.revoke') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
