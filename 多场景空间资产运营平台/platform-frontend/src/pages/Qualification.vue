<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const pageTitle = route.path === '/annual-reviews' ? '年审复核' : '资格复核'
const project = ref(null)
const contracts = ref([])
const selectedContractId = ref('')
const reviews = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ reviewYear: new Date().getFullYear(), reviewType: 'ANNUAL' })
const completeForm = reactive({ reviewId: '', result: 'PASSED', reviewerName: '复核员A', comment: '资格仍符合', nextReviewDate: '' })

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
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>{{ pageTitle }}</h2><p>{{ project.orgName }} · 合同年度资格复核</p></div>
          <select v-model="selectedContractId" style="max-width:340px">
            <option value="">选择合同</option>
            <option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.contractNo }} · {{ c.personName }}</option>
          </select>
        </div>
        <div class="row">
          <div class="field"><label>复核年度</label><input v-model.number="form.reviewYear" type="number" /></div>
          <div class="field"><label>类型</label><select v-model="form.reviewType"><option value="ANNUAL">年度复核</option><option value="CHANGE">变更复核</option></select></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">创建复核</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>复核记录</h2><span class="small muted">{{ reviews.length }} 条</span></div>
        <div v-if="!reviews.length" class="empty">暂无复核记录</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>年度</th><th>类型</th><th>状态</th><th>复核人</th><th>意见</th><th>复核日期</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="r in reviews" :key="r.id">
                <td>{{ r.reviewYear }}</td><td>{{ r.reviewType }}</td>
                <td><span class="badge" :class="r.reviewStatus === 'PASSED' ? 'green' : r.reviewStatus === 'FAILED' ? 'red' : 'orange'">{{ r.reviewStatus }}</span></td>
                <td>{{ r.reviewerName || '-' }}</td><td>{{ r.reviewComment || '-' }}</td><td>{{ r.reviewDate || '-' }}</td>
                <td><button class="sm" v-if="r.reviewStatus === 'PENDING'" :disabled="busy" @click="complete(r)">通过复核</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
