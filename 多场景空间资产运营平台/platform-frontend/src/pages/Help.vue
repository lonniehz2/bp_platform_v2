<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()
const version = 'v0.1.0'
const tenant = localStorage.getItem('platformUser') ? (JSON.parse(localStorage.getItem('platformUser') || '{}').tenantId || '350600') : '350600'
const sections = computed(() => [
  { title: t('help.section1'), items: [t('help.i11'), t('help.i12'), t('help.i13')] },
  { title: t('help.section2'), items: [t('help.i21'), t('help.i22'), t('help.i23'), t('help.i24')] },
  { title: t('help.section3'), items: [t('help.i31'), t('help.i32'), t('help.i33'), t('help.i34')] },
  { title: t('help.section4'), items: [t('help.i41'), t('help.i42'), t('help.i43'), t('help.i44')] },
  { title: t('help.section5'), items: [t('help.i51'), t('help.i52'), t('help.i53'), t('help.i54')] }
])
const currentTitle = computed(() => t(route.meta?.titleKey || 'help.title'))
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('help.title') }}</h2><p>{{ t('help.subtitle') }}</p></div><span class="badge blue">{{ version }}</span></div>
      <div class="grid cards">
        <div class="card"><div class="label">{{ t('help.current') }}</div><div class="value" style="font-size:18px">{{ currentTitle }}</div><div class="hint">{{ t('help.fromMenu') }}</div></div>
        <div class="card"><div class="label">{{ t('help.tenant') }}</div><div class="value" style="font-size:18px">{{ tenant }}</div><div class="hint">{{ t('help.tenantHint') }}</div></div>
        <div class="card"><div class="label">{{ t('help.frontend') }}</div><div class="value" style="font-size:18px">Vue 3</div><div class="hint">{{ t('help.frontendHint') }}</div></div>
        <div class="card"><div class="label">{{ t('help.backend') }}</div><div class="value" style="font-size:18px">Spring Boot 3</div><div class="hint">{{ t('help.backendHint') }}</div></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
      <div v-for="s in sections" :key="s.title" class="panel">
        <div class="panel-head"><h2>{{ s.title }}</h2></div>
        <div v-for="(item, i) in s.items" :key="item" class="row" style="padding:7px 0;border-bottom:1px solid var(--line)">
          <span class="badge blue">{{ i + 1 }}</span>
          <span class="small">{{ item }}</span>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('help.entries') }}</h2></div>
      <div class="row">
        <RouterLink class="badge blue" to="/projects">{{ t('help.projects') }}</RouterLink>
        <RouterLink class="badge blue" to="/applications">{{ t('help.applications') }}</RouterLink>
        <RouterLink class="badge blue" to="/contracts">{{ t('help.contracts') }}</RouterLink>
        <RouterLink class="badge blue" to="/billing">{{ t('help.billing') }}</RouterLink>
        <RouterLink class="badge blue" to="/audit">{{ t('help.audit') }}</RouterLink>
        <RouterLink class="badge blue" to="/users">{{ t('help.users') }}</RouterLink>
      </div>
    </div>
  </div>
</template>
