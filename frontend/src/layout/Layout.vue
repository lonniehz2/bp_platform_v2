<template>
  <component :is="shell" />
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { uiState } from './uiState'
import LayoutClassic from './LayoutClassic.vue'
import LayoutRail from './LayoutRail.vue'
import { useTodoStore } from '@/store/todo'

/** 两种风格共用同一路由树，切换只换外壳，页面内容完全一致 */
const shell = computed(() =>
  uiState.style === 'classic' ? LayoutClassic : LayoutRail)

// 待办角标：进入主框架即开始轮询，两种风格共用同一份计数
const todo = useTodoStore()
onMounted(() => todo.start())
</script>
