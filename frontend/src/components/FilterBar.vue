<template>
  <div class="bp-filter">
    <div class="bp-filter-row">
      <slot />
      <el-button type="primary" @click="$emit('search')" data-testid="filter-search">查询</el-button>
      <el-button @click="$emit('reset')" data-testid="filter-reset">清空</el-button>
      <el-button v-if="$slots.more" text type="primary"
                 @click="open = !open" data-testid="filter-more">
        {{ open ? '收起' : '更多筛选' }}
      </el-button>
    </div>
    <div v-if="$slots.more && open" class="bp-filter-more">
      <slot name="more" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

/**
 * 统一筛选栏。
 *
 * 用法：
 *   <FilterBar @search="reload" @reset="resetQuery">
 *     <el-input v-model="keyword" placeholder="关键字" />
 *     <template #more>
 *       <el-select v-model="status" placeholder="状态">…</el-select>
 *     </template>
 *   </FilterBar>
 *
 * 约定：
 *  - 默认展示最高频的 1–2 个条件，其余收进「更多筛选」，避免工具栏被撑爆
 *  - 查询/清空 由父组件实现，本组件只负责布局与展开状态
 */
defineEmits(['search', 'reset'])
const open = ref(false)
</script>

<style scoped>
.bp-filter { margin-bottom: 10px; }
.bp-filter-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.bp-filter-more {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
  padding: 8px 10px;
  background: #fafafa;
  border: 1px dashed #e8e8e8;
  border-radius: 2px;
}
</style>
