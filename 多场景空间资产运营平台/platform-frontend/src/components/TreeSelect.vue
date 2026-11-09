<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, null], default: null },
  nodes: { type: Array, default: () => [] },
  labelKey: { type: String, default: 'spaceName' },
  valueKey: { type: String, default: 'id' },
  parentKey: { type: String, default: 'parentId' },
  placeholder: { type: String, default: '请选择' },
  disabled: { type: Boolean, default: false },
  clearable: { type: Boolean, default: true }
})
const emit = defineEmits(['update:modelValue', 'change'])
const root = ref(null)
const search = ref(null)
const open = ref(false)
const query = ref('')
const expanded = ref(new Set())

const valueOf = (n) => n[props.valueKey] ?? n.id
const labelOf = (n) => String(n[props.labelKey] ?? n.label ?? '')
const parentOf = (n) => n[props.parentKey] ?? null
const byId = computed(() => {
  const map = new Map()
  for (const n of props.nodes) map.set(String(valueOf(n)), n)
  return map
})
const depthOf = (n) => {
  let d = 0; let p = parentOf(n); const seen = new Set()
  while (p != null && byId.value.has(String(p)) && !seen.has(String(p))) {
    seen.add(String(p)); d++; p = parentOf(byId.value.get(String(p)))
  }
  return d
}
const roots = computed(() => props.nodes.filter(n => parentOf(n) == null || !byId.value.has(String(parentOf(n)))))
const selected = computed(() => props.nodes.find(n => String(valueOf(n)) === String(props.modelValue)))
const selectedLabel = computed(() => {
  if (!selected.value) return ''
  const names = []; let n = selected.value; const seen = new Set()
  while (n) {
    names.unshift(labelOf(n));
    const p = parentOf(n)
    if (p == null || seen.has(String(p))) break
    seen.add(String(p)); n = byId.value.get(String(p))
  }
  return names.join(' / ')
})
const flat = computed(() => {
  const q = query.value.trim().toLowerCase()
  const rows = []
  const walk = (list) => {
    for (const n of list) {
      const match = !q || labelOf(n).toLowerCase().includes(q)
      if (match || q) rows.push({ node: n, depth: depthOf(n), hasChildren: props.nodes.some(x => String(parentOf(x)) === String(valueOf(n))) })
      const children = props.nodes.filter(x => String(parentOf(x)) === String(valueOf(n)))
      if (children.length && (q || expanded.value.has(String(valueOf(n))))) walk(children)
    }
  }
  if (q) {
    for (const n of props.nodes) if (labelOf(n).toLowerCase().includes(q)) rows.push({ node: n, depth: depthOf(n), hasChildren: false })
  } else walk(roots.value)
  return rows
})

watch(open, (v) => { if (v) { query.value = ''; nextTick(() => search.value?.focus()) } })
function toggle() { if (!props.disabled) open.value = !props.disabled }
function toggleNode(n) { const id = String(valueOf(n)); const s = new Set(expanded.value); s.has(id) ? s.delete(id) : s.add(id); expanded.value = s }
function choose(n) { emit('update:modelValue', valueOf(n)); emit('change', n); open.value = false }
function clear() { emit('update:modelValue', null); emit('change', null); open.value = false }
function outside(e) { if (root.value && !root.value.contains(e.target)) open.value = false }
onMounted(() => document.addEventListener('mousedown', outside))
onBeforeUnmount(() => document.removeEventListener('mousedown', outside))
</script>

<template>
  <div ref="root" class="ts" :class="{ open, disabled }" @click="toggle">
    <div class="ts-control">
      <span v-if="selectedLabel" class="ts-selected">{{ selectedLabel }}</span>
      <span v-else class="ts-placeholder">{{ placeholder }}</span>
      <button v-if="clearable && selectedLabel && !disabled" class="ts-clear" type="button" @click.stop="clear">×</button>
      <span class="ts-arrow">⌄</span>
    </div>
    <div v-if="open" class="ts-drop" @click.stop>
      <input ref="search" v-model="query" class="ts-search" placeholder="搜索空间/名称" @click.stop />
      <div v-if="!flat.length" class="ts-empty">没有匹配项</div>
      <button v-for="row in flat" :key="valueOf(row.node)" type="button" class="ts-node" :style="{ paddingLeft: (10 + row.depth * 16) + 'px' }" :class="{ selected: String(valueOf(row.node)) === String(modelValue) }" @click="choose(row.node)">
        <span v-if="row.hasChildren" class="ts-toggle" @click.stop="toggleNode(row.node)">{{ expanded.has(String(valueOf(row.node))) ? '⌄' : '›' }}</span>
        <span v-else class="ts-toggle-placeholder"></span>
        <span class="ts-node-label">{{ labelOf(row.node) }}</span>
        <span v-if="String(valueOf(row.node)) === String(modelValue)" class="ts-check">✓</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.ts { position: relative; width: 100%; font-size: 13px; }
.ts-control { display: flex; align-items: center; min-height: 34px; padding: 0 8px; border: 1px solid var(--line-strong); border-radius: 6px; background: var(--panel); cursor: pointer; }
.ts.open .ts-control { border-color: var(--brand); box-shadow: 0 0 0 2px rgba(24,144,255,.12); }
.ts.disabled { opacity: .55; pointer-events: none; }
.ts-selected { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--ink); }
.ts-placeholder { flex: 1; color: var(--muted); }
.ts-arrow { color: var(--muted); margin-left: 6px; }
.ts-clear { border: 0; background: transparent; color: var(--muted); padding: 0 4px; font-size: 15px; cursor: pointer; }
.ts-drop { position: absolute; z-index: 80; left: 0; right: 0; top: calc(100% + 4px); max-height: 320px; overflow: auto; padding: 5px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.12); }
.ts-search { width: 100%; height: 30px; margin-bottom: 4px; border: 1px solid var(--line); border-radius: 5px; padding: 0 8px; background: var(--bg); color: var(--ink); }
.ts-node { width: 100%; border: 0; background: transparent; display: flex; align-items: center; gap: 4px; min-height: 34px; padding: 5px 8px; border-radius: 5px; text-align: left; color: var(--regular); cursor: pointer; }
.ts-node:hover, .ts-node.selected { background: var(--brand-soft); color: var(--brand); }
.ts-toggle { width: 16px; color: var(--muted); font-size: 15px; text-align: center; }
.ts-toggle-placeholder { width: 16px; }
.ts-node-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ts-check { color: var(--brand); font-weight: 700; }
.ts-empty { padding: 12px; color: var(--muted); text-align: center; font-size: 12px; }
</style>
