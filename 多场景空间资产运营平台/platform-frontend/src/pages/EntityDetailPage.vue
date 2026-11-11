<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'

const route = useRoute()
const router = useRouter()
const type = computed(() => String(route.params.type || '').toUpperCase())
const id = computed(() => route.params.id)
const labels = { PERSON: '人员详情', HOUSE: '房源详情', BILL: '账单详情', DEVICE: '设备详情', WORK_ORDER: '工单详情', APPLICATION: '申请详情', CONTRACT: '合同详情' }
const label = computed(() => labels[type.value] || '详情')
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head">
        <div><h2>{{ label }}</h2><p class="small muted">关联信息统一 Tab 视图</p></div>
        <button class="sm" @click="router.back()">返回</button>
      </div>
    </div>
    <div class="panel">
      <EntityDetailTabs :type="type" :entity-id="id" />
    </div>
  </div>
</template>
