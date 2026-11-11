<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api'
import { useI18n } from 'vue-i18n'
import { sceneRoot } from '../scene'
import { contractTemplate, userTemplate, deviceGrantTemplate, grantTemplate, bindingTemplate, relationTemplate, spaceTemplate, personTemplate } from '../importTemplates'

const { t, locale } = useI18n()
const personFile = ref(null)
const personBusy = ref(false)
const personResult = ref(null)
const personError = ref('')
const spaceFile = ref(null)
const spaceBusy = ref(false)
const spaceResult = ref(null)
const spaceError = ref('')
const relationFile = ref(null)
const relationBusy = ref(false)
const relationResult = ref(null)
const relationError = ref('')
const bindingFile = ref(null)
const bindingBusy = ref(false)
const bindingResult = ref(null)
const bindingError = ref('')
const grantFile = ref(null)
const grantBusy = ref(false)
const grantResult = ref(null)
const grantError = ref('')
const deviceGrantFile = ref(null)
const deviceGrantBusy = ref(false)
const deviceGrantResult = ref(null)
const deviceGrantError = ref('')
const userFile = ref(null)
const userBusy = ref(false)
const userResult = ref(null)
const userError = ref('')
const contractFile = ref(null)
const contractBusy = ref(false)
const contractResult = ref(null)
const contractError = ref('')

function pickPerson(e) { personFile.value = e.target.files?.[0] || null; personResult.value = null; personError.value = '' }

function pickContract(e) { contractFile.value = e.target.files?.[0] || null; contractResult.value = null; contractError.value = '' }

function downloadContractTemplate() {
  const csv = contractTemplate(locale.value === 'en-US')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = t('imp.contractTemplate') + '.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importContracts() {
  if (!contractFile.value) { contractError.value = t('imp.requiredFile'); return }
  contractBusy.value = true; contractError.value = ''; contractResult.value = null
  try { contractResult.value = await api.importContracts(contractFile.value) } catch (e) { contractError.value = e.message } finally { contractBusy.value = false }
}

function pickUser(e) { userFile.value = e.target.files?.[0] || null; userResult.value = null; userError.value = '' }

function downloadUserTemplate() {
  const csv = userTemplate(locale.value === 'en-US')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = t('imp.userTemplate') + '.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importUsers() {
  if (!userFile.value) { userError.value = t('imp.requiredFile'); return }
  userBusy.value = true; userError.value = ''; userResult.value = null
  try { userResult.value = await api.importUsers(userFile.value) } catch (e) { userError.value = e.message } finally { userBusy.value = false }
}

function pickDeviceGrant(e) { deviceGrantFile.value = e.target.files?.[0] || null; deviceGrantResult.value = null; deviceGrantError.value = '' }

function downloadDeviceGrantTemplate() {
  const csv = deviceGrantTemplate(locale.value === 'en-US')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = t('imp.deviceGrantTemplate') + '.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importDeviceGrants() {
  if (!deviceGrantFile.value) { deviceGrantError.value = t('imp.requiredFile'); return }
  deviceGrantBusy.value = true; deviceGrantError.value = ''; deviceGrantResult.value = null
  try { deviceGrantResult.value = await api.importDeviceGrants(deviceGrantFile.value) } catch (e) { deviceGrantError.value = e.message } finally { deviceGrantBusy.value = false }
}

function pickGrant(e) { grantFile.value = e.target.files?.[0] || null; grantResult.value = null; grantError.value = '' }

function downloadGrantTemplate() {
  const csv = grantTemplate(locale.value === 'en-US')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = t('imp.grantTemplate') + '.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importGrants() {
  if (!grantFile.value) { grantError.value = t('imp.requiredFile'); return }
  grantBusy.value = true; grantError.value = ''; grantResult.value = null
  try { grantResult.value = await api.importSpaceGrants(grantFile.value) } catch (e) { grantError.value = e.message } finally { grantBusy.value = false }
}

function pickBinding(e) { bindingFile.value = e.target.files?.[0] || null; bindingResult.value = null; bindingError.value = '' }

function downloadBindingTemplate() {
  const csv = bindingTemplate(locale.value === 'en-US')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = t('imp.bindingTemplate') + '.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importBindings() {
  if (!bindingFile.value) { bindingError.value = t('imp.requiredFile'); return }
  bindingBusy.value = true; bindingError.value = ''; bindingResult.value = null
  try { bindingResult.value = await api.importDeviceBindings(bindingFile.value) } catch (e) { bindingError.value = e.message } finally { bindingBusy.value = false }
}

function pickRelation(e) { relationFile.value = e.target.files?.[0] || null; relationResult.value = null; relationError.value = '' }

function downloadRelationTemplate() {
  const csv = relationTemplate(locale.value === 'en-US')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = t('imp.relationTemplate') + '.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importRelations() {
  if (!relationFile.value) { relationError.value = t('imp.requiredFile'); return }
  relationBusy.value = true; relationError.value = ''; relationResult.value = null
  try { relationResult.value = await api.importPersonAssets(relationFile.value) } catch (e) { relationError.value = e.message } finally { relationBusy.value = false }
}

function pickSpace(e) { spaceFile.value = e.target.files?.[0] || null; spaceResult.value = null; spaceError.value = '' }

function downloadSpaceTemplate() {
  const csv = spaceTemplate(locale.value === 'en-US')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = t('imp.spaceTemplate') + '.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importSpaces() {
  if (!spaceFile.value) { spaceError.value = t('imp.requiredFile'); return }
  spaceBusy.value = true; spaceError.value = ''; spaceResult.value = null
  try { spaceResult.value = await api.importSpaces(spaceFile.value) } catch (e) { spaceError.value = e.message } finally { spaceBusy.value = false }
}

function downloadPersonTemplate() {
  const csv = personTemplate(locale.value === 'en-US')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = t('imp.personTemplate') + '.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importPersons() {
  if (!personFile.value) { personError.value = t('imp.requiredFile'); return }
  personBusy.value = true; personError.value = ''; personResult.value = null
  try { personResult.value = await api.importPersons(personFile.value) } catch (e) { personError.value = e.message } finally { personBusy.value = false }
}
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('imp.title') }}</h2><p>{{ t('imp.subtitle') }}</p></div><span class="pill">{{ t('imp.title') }}</span></div>
      <div class="alert">{{ t('imp.hint') }}</div>
    </div>

    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.person') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadPersonTemplate">{{ t('imp.download') }}</button><input type="file" accept=".csv" @change="pickPerson" /><span class="small muted">{{ personFile?.name || t('imp.noFile') }}</span></div>
        <div v-if="personError" class="error">{{ personError }}</div>
        <button class="primary" :disabled="personBusy || !personFile" @click="importPersons">{{ personBusy ? t('imp.importing') : t('imp.start') }}</button>
        <div v-if="personResult" style="margin-top:12px">
          <div class="alert" :class="personResult.failed ? 'warn' : 'ok'">{{ t('imp.total', { n: personResult.total }) }} · {{ t('imp.success', { n: personResult.success }) }} · {{ t('imp.failed', { n: personResult.failed }) }}</div>
          <div v-if="personResult.errors?.length" class="table-wrap" style="margin-top:8px">
            <table><thead><tr><th>{{ t('imp.line') }}</th><th>{{ t('imp.reason') }}</th></tr></thead><tbody><tr v-for="e in personResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.space') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadSpaceTemplate">{{ t('imp.download') }}</button><input type="file" accept=".csv" @change="pickSpace" /><span class="small muted">{{ spaceFile?.name || t('imp.noFile') }}</span></div>
        <div v-if="spaceError" class="error">{{ spaceError }}</div>
        <button class="primary" :disabled="spaceBusy || !spaceFile" @click="importSpaces">{{ spaceBusy ? t('imp.importing') : t('imp.start') }}</button>
        <div v-if="spaceResult" style="margin-top:12px">
          <div class="alert" :class="spaceResult.failed ? 'warn' : 'ok'">{{ t('imp.total', { n: spaceResult.total }) }} · {{ t('imp.success', { n: spaceResult.success }) }} · {{ t('imp.failed', { n: spaceResult.failed }) }}</div>
          <div v-if="spaceResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>{{ t('imp.line') }}</th><th>{{ t('imp.reason') }}</th></tr></thead><tbody><tr v-for="e in spaceResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.relation') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadRelationTemplate">{{ t('imp.download') }}</button><input type="file" accept=".csv" @change="pickRelation" /><span class="small muted">{{ relationFile?.name || t('imp.noFile') }}</span></div>
        <div v-if="relationError" class="error">{{ relationError }}</div>
        <button class="primary" :disabled="relationBusy || !relationFile" @click="importRelations">{{ relationBusy ? t('imp.importing') : t('imp.start') }}</button>
        <div v-if="relationResult" style="margin-top:12px">
          <div class="alert" :class="relationResult.failed ? 'warn' : 'ok'">{{ t('imp.total', { n: relationResult.total }) }} · {{ t('imp.success', { n: relationResult.success }) }} · {{ t('imp.failed', { n: relationResult.failed }) }}</div>
          <div v-if="relationResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>{{ t('imp.line') }}</th><th>{{ t('imp.reason') }}</th></tr></thead><tbody><tr v-for="e in relationResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.grant') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadGrantTemplate">{{ t('imp.download') }}</button><input type="file" accept=".csv" @change="pickGrant" /><span class="small muted">{{ grantFile?.name || t('imp.noFile') }}</span></div>
        <div v-if="grantError" class="error">{{ grantError }}</div>
        <button class="primary" :disabled="grantBusy || !grantFile" @click="importGrants">{{ grantBusy ? t('imp.importing') : t('imp.start') }}</button>
        <div v-if="grantResult" style="margin-top:12px">
          <div class="alert" :class="grantResult.failed ? 'warn' : 'ok'">{{ t('imp.total', { n: grantResult.total }) }} · {{ t('imp.success', { n: grantResult.success }) }} · {{ t('imp.failed', { n: grantResult.failed }) }}</div>
          <div v-if="grantResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>{{ t('imp.line') }}</th><th>{{ t('imp.reason') }}</th></tr></thead><tbody><tr v-for="e in grantResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.contract') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadContractTemplate">{{ t('imp.download') }}</button><input type="file" accept=".csv" @change="pickContract" /><span class="small muted">{{ contractFile?.name || t('imp.noFile') }}</span></div>
        <div v-if="contractError" class="error">{{ contractError }}</div>
        <button class="primary" :disabled="contractBusy || !contractFile" @click="importContracts">{{ contractBusy ? t('imp.importing') : t('imp.start') }}</button>
        <div v-if="contractResult" style="margin-top:12px">
          <div class="alert" :class="contractResult.failed ? 'warn' : 'ok'">{{ t('imp.total', { n: contractResult.total }) }} · {{ t('imp.success', { n: contractResult.success }) }} · {{ t('imp.failed', { n: contractResult.failed }) }}</div>
          <div v-if="contractResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>{{ t('imp.line') }}</th><th>{{ t('imp.reason') }}</th></tr></thead><tbody><tr v-for="e in contractResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.user') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadUserTemplate">{{ t('imp.download') }}</button><input type="file" accept=".csv" @change="pickUser" /><span class="small muted">{{ userFile?.name || t('imp.noFile') }}</span></div>
        <div v-if="userError" class="error">{{ userError }}</div>
        <button class="primary" :disabled="userBusy || !userFile" @click="importUsers">{{ userBusy ? t('imp.importing') : t('imp.start') }}</button>
        <div v-if="userResult" style="margin-top:12px">
          <div class="alert" :class="userResult.failed ? 'warn' : 'ok'">{{ t('imp.total', { n: userResult.total }) }} · {{ t('imp.success', { n: userResult.success }) }} · {{ t('imp.failed', { n: userResult.failed }) }}</div>
          <div v-if="userResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>{{ t('imp.line') }}</th><th>{{ t('imp.reason') }}</th></tr></thead><tbody><tr v-for="e in userResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.deviceGrant') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadDeviceGrantTemplate">{{ t('imp.download') }}</button><input type="file" accept=".csv" @change="pickDeviceGrant" /><span class="small muted">{{ deviceGrantFile?.name || t('imp.noFile') }}</span></div>
        <div v-if="deviceGrantError" class="error">{{ deviceGrantError }}</div>
        <button class="primary" :disabled="deviceGrantBusy || !deviceGrantFile" @click="importDeviceGrants">{{ deviceGrantBusy ? t('imp.importing') : t('imp.start') }}</button>
        <div v-if="deviceGrantResult" style="margin-top:12px">
          <div class="alert" :class="deviceGrantResult.failed ? 'warn' : 'ok'">{{ t('imp.total', { n: deviceGrantResult.total }) }} · {{ t('imp.success', { n: deviceGrantResult.success }) }} · {{ t('imp.failed', { n: deviceGrantResult.failed }) }}</div>
          <div v-if="deviceGrantResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>{{ t('imp.line') }}</th><th>{{ t('imp.reason') }}</th></tr></thead><tbody><tr v-for="e in deviceGrantResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.binding') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadBindingTemplate">{{ t('imp.download') }}</button><input type="file" accept=".csv" @change="pickBinding" /><span class="small muted">{{ bindingFile?.name || t('imp.noFile') }}</span></div>
        <div v-if="bindingError" class="error">{{ bindingError }}</div>
        <button class="primary" :disabled="bindingBusy || !bindingFile" @click="importBindings">{{ bindingBusy ? t('imp.importing') : t('imp.start') }}</button>
        <div v-if="bindingResult" style="margin-top:12px">
          <div class="alert" :class="bindingResult.failed ? 'warn' : 'ok'">{{ t('imp.total', { n: bindingResult.total }) }} · {{ t('imp.success', { n: bindingResult.success }) }} · {{ t('imp.failed', { n: bindingResult.failed }) }}</div>
          <div v-if="bindingResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>{{ t('imp.line') }}</th><th>{{ t('imp.reason') }}</th></tr></thead><tbody><tr v-for="e in bindingResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('imp.device') }}</h2><span class="small muted">{{ t('imp.csv') }}</span></div>
        <p class="muted">{{ t('imp.deviceHint') }}</p>
        <RouterLink class="primary" :to="sceneRoot() + '/device-bind'">{{ t('imp.goBind') }}</RouterLink>
      </div>
    </div>
  </div>
</template>
