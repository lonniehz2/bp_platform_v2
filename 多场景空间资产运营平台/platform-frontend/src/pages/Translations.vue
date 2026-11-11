<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '../i18n'
import { businessTerms } from '../translationDictionary'

const { locale, t } = useI18n()
const keyword = ref('')
const terms = businessTerms
const filtered = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return q ? terms.filter(t => t.some(v => String(v).toLowerCase().includes(q))) : terms
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('translations.title') }}</h2><p>{{ t('translations.subtitle') }}</p></div>
        <div class="row">
          <button class="sm" :class="{ primary: locale === 'zh-CN' }" @click="setLocale('zh-CN')">{{ t('translations.zhShort') }}</button>
          <button class="sm" :class="{ primary: locale === 'en-US' }" @click="setLocale('en-US')">English</button>
        </div>
      </div>
      <div class="field" style="max-width:360px"><label>{{ t('translations.query') }}</label><input v-model="keyword" :placeholder="t('translations.searchPlaceholder')" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('translations.list') }}</h2><span class="small muted">{{ filtered.length }} {{ t('translations.count') }}</span></div>
      <div class="table-wrap">
        <table data-no-i18n>
          <thead><tr><th>{{ t('translations.code') }}</th><th>{{ t('translations.chineseCol') }}</th><th>English</th></tr></thead>
          <tbody>
            <tr v-for="t in filtered" :key="t[0]">
              <td class="mono">{{ t[0] }}</td><td>{{ t[1] }}</td><td>{{ t[2] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="alert" style="margin-top:12px">{{ t('translations.note') }}</div>
    </div>
  </div>
</template>
