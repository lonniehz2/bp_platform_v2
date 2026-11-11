<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { confirmAction } from '../confirm'
import TreeSelect from '../components/TreeSelect.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const persons = ref([])
const spaces = ref([])
const grants = ref([])
const personId = ref('')
const error = ref('')
const busy = ref(false)
const form = reactive({ targetId: '', validStart: '2026-11-08', validEnd: '2027-11-07' })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const [p, s] = await Promise.all([api.persons(), api.spaces(project.value.id)])
    persons.value = p; spaces.value = s
    if (!personId.value && p.length) personId.value = p[0].id
    if (!form.targetId && s.length) form.targetId = s[0].id
    await loadGrants()
  } catch (e) { error.value = e.message }
}

async function loadGrants() {
  if (!personId.value) { grants.value = []; return }
  try { grants.value = await api.grants(personId.value, project.value?.id) } catch { grants.value = [] }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!personId.value || !form.targetId) throw new Error(t('grants.required'))
    await api.createGrant({
      projectId: project.value.id, personId: personId.value, targetType: 'SPACE', targetId: form.targetId,
      grantLevel: 'OPEN', validStart: form.validStart, validEnd: form.validEnd, sourceType: 'MANUAL'
    })
    await loadGrants()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function revoke(g) {
  if (!await confirmAction({ title: t('grants.revokeTitle'), message: t('grants.revokeMessage'), confirmText: t('grants.revokeConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.revokeGrant(g.id, t('grants.revokeReason')); await loadGrants() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('grants.title') }}</h2><p>{{ project?.orgName || t('grants.noProject') }} · {{ t('grants.subtitle') }}</p></div><span class="badge blue">{{ grants.length }} {{ t('grants.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('grants.person') }}</label><SearchSelect v-model="personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('grants.searchPerson')" @change="loadGrants" /></div>
        <div class="field"><label>{{ t('grants.target') }}</label><TreeSelect v-model="form.targetId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" :placeholder="t('grants.selectTarget')" /></div>
        <div class="field"><label>{{ t('grants.start') }}</label><input v-model="form.validStart" type="date" /></div>
        <div class="field"><label>{{ t('grants.end') }}</label><input v-model="form.validEnd" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">{{ t('grants.add') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('grants.list') }}</h2><span class="small muted">{{ t('grants.hint') }}</span></div>
      <div v-if="!grants.length" class="empty">{{ t('grants.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('grants.type') }}</th><th>{{ t('grants.object') }}</th><th>{{ t('grants.level') }}</th><th>{{ t('grants.validity') }}</th><th>{{ t('grants.status') }}</th><th>{{ t('grants.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="g in grants" :key="g.id">
              <td>{{ g.targetType }}</td><td class="mono">{{ g.targetId }}</td><td>{{ g.grantLevel }}</td>
              <td class="small">{{ g.validStart }} ~ {{ g.validEnd || t('grants.longTerm') }}</td>
              <td><span class="badge" :class="g.grantStatus === 'ACTIVE' ? 'green' : 'orange'">{{ g.grantStatus }}</span></td>
              <td><button v-if="g.grantStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="revoke(g)">{{ t('grants.revoke') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
