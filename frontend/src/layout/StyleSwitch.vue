<template>
  <el-tooltip :content="`当前：${uiState.style === 'rail' ? '风格2 · 图标窄栏' : '风格1 · 宽侧栏'}（点击切换）`">
    <el-segmented v-model="model" :options="options" size="small"
                  style="margin-right:8px" />
  </el-tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { uiState, setStyle } from './uiState'

const options = [
  { label: '风格1', value: 'classic' },
  { label: '风格2', value: 'rail' }
]

const model = computed({
  get: () => uiState.style,
  set: (v) => setStyle(v)
})
</script>
