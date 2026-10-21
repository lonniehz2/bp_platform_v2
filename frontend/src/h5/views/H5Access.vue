<template>
  <div>
    <div class="navbar"><span class="back" @click="$router.back()">←</span>我的开门记录</div>

    <div class="card">
      <div class="row"><b>不可信开门占比</b><div class="spacer" />
        <el-tag size="small" :type="ratio.pass ? 'success' : 'danger'">
          {{ ratio.pass ? '达标' : '超标' }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">
        {{ ratio.untrusted }} / {{ ratio.total }} 次 · 占比 {{ ratio.untrustedRatio }}%
        （阈值 {{ ratio.threshold }}%）
      </div>
    </div>

    <div v-for="r in rows" :key="r.id" class="card">
      <div class="row">
        <b>{{ r.openTypeName }}</b>
        <div class="spacer" />
        <el-tag v-if="r.abnormal" type="danger" size="small">异常</el-tag>
        <el-tag v-else-if="!r.trusted" type="warning" size="small">不可信</el-tag>
      </div>
      <div class="muted" style="margin-top:6px">{{ r.openTime }} · 门锁 {{ r.lockId }}</div>
    </div>

    <div v-if="!rows.length" class="empty">暂无开门记录</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { devApi } from '@/api/modules'

const rows = ref([])
const ratio = ref({})
const personId = localStorage.getItem('bp_person_id') || ''

onMounted(async () => {
  const data = await devApi.accessRecords({
    pageNum: 1, pageSize: 50, personId: personId || undefined
  })
  rows.value = data.rows || []
  ratio.value = await devApi.untrustedRatio()
})
</script>
