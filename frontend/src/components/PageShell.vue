<template>
  <div class="bp-page">
    <div class="bp-page-head">
      <div>
        <h2>{{ title }}</h2>
        <div v-if="desc" class="desc">{{ desc }}</div>
      </div>
      <div class="actions">
        <slot name="actions" />
      </div>
    </div>

    <!-- 搜索/筛选区 -->
    <div v-if="$slots.search" class="bp-card">
      <div class="bp-search">
        <slot name="search" />
      </div>
    </div>

    <!-- 主内容 -->
    <div class="bp-card">
      <div v-if="$slots.title || $slots.toolbar" class="head">
        <slot name="title" />
        <div class="actions">
          <slot name="toolbar" />
        </div>
      </div>
      <slot />
    </div>

    <slot name="extra" />
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  desc: { type: String, default: '' }
})
</script>
