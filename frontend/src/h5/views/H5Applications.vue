<template>
  <div>
    <div class="navbar">申请进度</div>

    <el-steps v-if="current" :active="stepOf(current)" simple style="margin:12px">
      <el-step title="提交" />
      <el-step title="受理" />
      <el-step title="审核" />
      <el-step title="结果" />
    </el-steps>

    <div v-for="a in rows" :key="a.id" class="card">
      <div class="row">
        <b>{{ a.applicationNo }}</b>
        <div class="spacer" />
        <el-tag size="small" :type="tagOf(a.applicationStatus)">
          {{ a.applicationStatusLabel || a.applicationStatus }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">
        {{ a.securityType }} · 家庭 {{ a.familySize }} 人 · 人均收入 ¥{{ a.incomePerCapita }}
      </div>
      <div class="muted" style="margin-top:4px">当前环节：{{ a.currentNode || '-' }}</div>
      <div v-if="a.rejectReason" style="margin-top:6px;color:#f53f3f;font-size:12px">
        不通过原因：{{ a.rejectReason }}
      </div>
      <div v-if="a.supplementDemand" style="margin-top:6px;color:#ff7d00;font-size:12px">
        需补件：{{ a.supplementDemand }}
      </div>
      <div class="muted" style="margin-top:6px">申请时间 {{ a.applyTime }}</div>
    </div>

    <div v-if="!rows.length" class="empty">暂无申请记录</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { applicationApi } from '@/api/modules'

const rows = ref([])
const personId = localStorage.getItem('bp_person_id') || ''
const current = computed(() => rows.value[0])

function stepOf(a) {
  const s = a.applicationStatus
  if (['APPROVED', 'REJECTED'].includes(s)) return 4
  if (['REVIEWING', 'SUPPLEMENT'].includes(s)) return 3
  if (s === 'ACCEPTED') return 2
  return 1
}
function tagOf(s) {
  return ({ APPROVED: 'success', REJECTED: 'danger',
    SUPPLEMENT: 'warning' })[s] || 'info'
}

onMounted(async () => {
  const data = await applicationApi.page({
    pageNum: 1, pageSize: 20, personId: personId || undefined
  })
  rows.value = data.rows || []
})
</script>
