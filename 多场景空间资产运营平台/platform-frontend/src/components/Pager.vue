<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  size: { type: Number, default: 10 }
})
const emit = defineEmits(['update:page'])
const pages = computed(() => Math.max(1, Math.ceil(props.total / props.size)))
const from = computed(() => props.total === 0 ? 0 : (props.page - 1) * props.size + 1)
const to = computed(() => Math.min(props.page * props.size, props.total))

function go(p) {
  if (p < 1 || p > pages.value || p === props.page) return
  emit('update:page', p)
}
</script>

<template>
  <div class="pager">
    <span class="small muted">共 {{ total }} 条 · {{ from }}-{{ to }} / {{ pages }} 页</span>
    <div class="row" style="gap:6px">
      <button class="sm" :disabled="page <= 1" @click="go(page - 1)">上一页</button>
      <span class="small">{{ page }}</span>
      <button class="sm" :disabled="page >= pages" @click="go(page + 1)">下一页</button>
    </div>
  </div>
</template>
