<template>
  <div>
    <div class="navbar"><span class="back" @click="$router.back()">←</span>{{ t('h5.accessTitle') }}</div>

    <div class="card">
      <div class="row"><b>{{ t('h5.untrustedRatio') }}</b><div class="spacer" />
        <el-tag size="small" :type="ratio.pass ? 'success' : 'danger'">
          {{ ratio.pass ? t('h5.pass') : t('h5.fail') }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">
        {{ t('h5.accessCount', { untrusted: ratio.untrusted, total: ratio.total, ratio: ratio.untrustedRatio }) }}
        {{ t('h5.threshold', { n: ratio.threshold }) }}
      </div>
    </div>

    <div v-for="r in rows" :key="r.id" class="card">
      <div class="row">
        <b>{{ r.openTypeName }}</b>
        <div class="spacer" />
        <el-tag v-if="r.abnormal" type="danger" size="small">{{ t('h5.abnormal') }}</el-tag>
        <el-tag v-else-if="!r.trusted" type="warning" size="small">{{ t('h5.untrusted') }}</el-tag>
      </div>
      <div class="muted" style="margin-top:6px">{{ r.openTime }} · {{ t('h5.lock', { id: r.lockId }) }}</div>
    </div>

    <div v-if="!rows.length" class="empty">{{ t('h5.noAccess') }}</div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
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
