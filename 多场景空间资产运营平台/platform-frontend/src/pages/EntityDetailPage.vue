<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const type = computed(() => String(route.params.type || '').toUpperCase())
const id = computed(() => route.params.id)
const labels = { PERSON: t('detail.person'), HOUSE: t('detail.house'), BILL: t('detail.bill'), DEVICE: t('detail.device'), WORK_ORDER: t('detail.workOrder'), APPLICATION: t('detail.application'), CONTRACT: t('detail.contract') }
const label = computed(() => labels[type.value] || t('detail.title'))
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head">
        <div><h2>{{ label }}</h2><p class="small muted">{{ t('detail.subtitle') }}</p></div>
        <button class="sm" @click="router.back()">{{ t('detail.back') }}</button>
      </div>
    </div>
    <div class="panel">
      <EntityDetailTabs :type="type" :entity-id="id" />
    </div>
  </div>
</template>
