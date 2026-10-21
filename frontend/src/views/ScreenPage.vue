<template>
  <div class="screen-host">
    <ScreenApp />
  </div>
</template>

<script setup>
/**
 * SPA 内的大屏路由包装页。
 *
 * 为什么需要它：ScreenApp.vue 的布局完全依赖 screen.css
 * （.screen-wrap 100vh、.screen-body grid-template-rows: auto 1fr 等）。
 * 该 CSS 原本只在独立入口 src/screen/main.js 引入，
 * 因此通过路由 /screen 在 SPA 内渲染时没有样式，图表容器高度塌陷为 0，
 * 表现为「只有空白，没有图表」。
 *
 * 独立入口 view-screen.html 一直是正常的，所以也在 Layout 里把按钮
 * 直接指向 view-screen.html，双路径都可用。
 */
import ScreenApp from '@/screen/ScreenApp.vue'
import '@/screen/screen.css'
</script>

<style scoped>
/* 覆盖整个视口：ScreenApp 自身是 100vw/100vh 的全屏布局，
   若嵌在 Layout 的内容区会被侧边栏挤压导致比例错乱 */
.screen-host {
  position: fixed;
  inset: 0;
  z-index: 2000;
  overflow: hidden;
  background: #050d1a;
}
</style>
