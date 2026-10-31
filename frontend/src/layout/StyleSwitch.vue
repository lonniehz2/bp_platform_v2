<template>
  <el-tooltip :content="uiState.mode === 'dark' ? t('layout.toLight') : t('layout.toDark')">
    <el-button circle size="small" style="margin-right:8px" @click="toggleMode">
      <el-icon><Moon v-if="uiState.mode === 'light'" /><Sunny v-else /></el-icon>
    </el-button>
  </el-tooltip>
  <el-tooltip :content="t('layout.styleTip', { name: uiState.style === 'rail' ? t('layout.railName') : t('layout.classicName') })">
    <el-segmented v-model="model" :options="options" size="small"
                  style="margin-right:8px" />
  </el-tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { uiState, setStyle, toggleMode } from './uiState'

const { t } = useI18n()
const options = computed(() => [
  { label: t('layout.style1'), value: 'classic' },
  { label: t('layout.style2'), value: 'rail' }
])

const model = computed({
  get: () => uiState.style,
  set: (v) => setStyle(v)
})
</script>
