<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { enumLabel } from '../enumLabels'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()
const pageTitle = computed(() => route.path === '/annual-reviews' ? t('qualification.annual') : t('qualification.title'))
const project = ref(null)
const contracts = ref([])
const selectedContractId = ref('')
const reviews = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ reviewYear: new Date().getFullYear(), reviewType: 'ANNUAL' })
const completeForm = reactive({ reviewId: '', result: 'PASSED', reviewerName: t('qualification.reviewerName'), comment: t('qualification.commentText'), nextReviewDate: '' })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  return chosen || all.slice().sort((a, b) =>
    ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
    ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
  )[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    contracts.value = await api.contracts(project.value.id)
    if (!selectedContractId.value && contracts.value.length) selectedContractId.value = contracts.value[0].id
    await loadReviews()
  } catch (e) { error.value = e.message }
}

async function loadReviews() {
  if (!selectedContractId.value) return
  reviews.value = await api.qualificationReviews(selectedContractId.value)
}

async function create() {
  busy.value = true; error.value = ''
  try {
    await api.createQualificationReview(selectedContractId.value, {
      reviewType: form.reviewType, reviewYear: Number(form.reviewYear)
    })
    await loadReviews()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function complete(r) {
  busy.value = true; error.value = ''
  try {
    await api.completeQualificationReview(r.id, {
      result: completeForm.result, reviewerName: completeForm.reviewerName,
      comment: completeForm.comment, nextReviewDate: completeForm.nextReviewDate || null
    })
    await loadReviews()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

watch(selectedContractId, loadReviews)
onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">{{ t('qualification.createProject') }}</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>{{ pageTitle }}</h2><p>{{ project.orgName }} · {{ t('qualification.subtitle') }}</p></div>
          <select v-model="selectedContractId" style="max-width:340px">
            <option value="">{{ t('qualification.selectContract') }}</option>
            <option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.contractNo }} · {{ c.personName }}</option>
          </select>
        </div>
        <div class="row">
          <div class="field"><label>{{ t('qualification.year') }}</label><input v-model.number="form.reviewYear" type="number" /></div>
          <div class="field"><label>{{ t('qualification.type') }}</label><select v-model="form.reviewType"><option value="ANNUAL">{{ t('qualification.annualType') }}</option><option value="CHANGE">{{ t('qualification.changeType') }}</option></select></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">{{ t('qualification.create') }}</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('qualification.records') }}</h2><span class="small muted">{{ reviews.length }} {{ t('qualification.count') }}</span></div>
        <div v-if="!reviews.length" class="empty">{{ t('qualification.empty') }}</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>{{ t('qualification.yearCol') }}</th><th>{{ t('qualification.type') }}</th><th>{{ t('qualification.status') }}</th><th>{{ t('qualification.reviewer') }}</th><th>{{ t('qualification.comment') }}</th><th>{{ t('qualification.date') }}</th><th>{{ t('qualification.action') }}</th></tr></thead>
            <tbody>
              <tr v-for="r in reviews" :key="r.id">
                <td>{{ r.reviewYear }}</td><td>{{ enumLabel(r.reviewType) }}</td>
                <td><span class="badge" :class="r.reviewStatus === 'PASSED' ? 'green' : r.reviewStatus === 'FAILED' ? 'red' : 'orange'">{{ enumLabel(r.reviewStatus) }}</span></td>
                <td>{{ r.reviewerName || '-' }}</td><td>{{ r.reviewComment || '-' }}</td><td>{{ r.reviewDate || '-' }}</td>
                <td><button class="sm" v-if="r.reviewStatus === 'PENDING'" :disabled="busy" @click="complete(r)">{{ t('qualification.approve') }}</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
