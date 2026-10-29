<template>
  <el-tooltip :content="uiState.mode === 'dark' ? '切换到浅色模式' : '切换到深色模式'">
    <el-button circle size="small" style="margin-right:8px" @click="toggleMode">
      <el-icon><Moon v-if="uiState.mode === 'light'" /><Sunny v-else /></el-icon>
    </el-button>
  </el-tooltip>
  <el-tooltip :content="`当前：${uiState.style === 'rail' ? '风格2 · 图标窄栏' : '风格1 · 宽侧栏'}（点击切换）`">
    <el-segmented v-model="model" :options="options" size="small"
                  style="margin-right:8px" />
  </el-tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { uiState, setStyle, toggleMode } from './uiState'

const options = [
  { label: '风格1', value: 'classic' },
  { label: '风格2', value: 'rail' }
]

const model = computed({
  get: () => uiState.style,
  set: (v) => setStyle(v)
})
</script>
