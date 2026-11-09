import io
p=r'src\components\SearchSelect.vue'
content='''<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, Array, null], default: null },
  options: { type: Array, default: () => [] },
  labelKey: { type: String, default: 'label' },
  sublabelKey: { type: String, default: '' },
  valueKey: { type: String, default: 'value' },
  placeholder: { type: String, default: '请选择' },
  multiple: { type: Boolean, default: false },
  clearable: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'change'])
const root = ref(null)
const control = ref(null)
const search = ref(null)
const open = ref(false)
const query = ref('')
const active = ref(0)

const labelOf = (o) => o ? String(o[props.labelKey] ?? o.label ?? '') : ''
const subOf = (o) => props.sublabelKey && o ? String(o[props.sublabelKey] ?? '') : ''
const valueOf = (o) => o ? o[props.valueKey] ?? o.value ?? o.id : null
const selectedValues = computed(() => Array.isArray(props.modelValue) ? props.modelValue : (props.modelValue == null || props.modelValue === '' ? [] : [props.modelValue]))
const selectedOptions = computed(() => props.options.filter(o => selectedValues.value.some(v => String(v) === String(valueOf(o)))))
const selectedLabel = computed(() => selectedOptions.value.map(labelOf).join('、'))
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return props.options.slice(0, 100)
  return props.options.filter(o => (labelOf(o) + ' ' + subOf(o)).toLowerCase().includes(q)).slice(0, 100)
})

watch(open, (v) => { if (v) { query.value = ''; active.value = 0; nextTick(() => search.value?.focus()) } })
watch(filtered, () => { active.value = 0 })

function toggle() { if (!props.disabled) open.value = !open.value }
function choose(o) {
  if (!o) return
  if (props.multiple) {
    const exists = selectedValues.value.some(v => String(v) === String(valueOf(o)))
    const next = exists ? selectedValues.value.filter(v => String(v) !== String(valueOf(o))) : [...selectedValues.value, valueOf(o)]
    emit('update:modelValue', next); emit('change', next)
  } else {
    emit('update:modelValue', valueOf(o)); emit('change', o); open.value = false
  }
}
function clear() {
  emit('update:modelValue', props.multiple ? [] : null)
  emit('change', props.multiple ? [] : null)
  open.value = false
}
function onKeydown(e) {
  if (e.key === 'Escape') { open.value = false; return }
  if (e.key === 'ArrowDown') { e.preventDefault(); active.value = Math.min(active.value + 1, filtered.value.length - 1) }
  if (e.key === 'ArrowUp') { e.preventDefault(); active.value = Math.max(active.value - 1, 0) }
  if (e.key === 'Enter') { e.preventDefault(); choose(filtered.value[active.value]) }
}
function outside(e) { if (root.value && !root.value.contains(e.target)) open.value = false }
onMounted(() => document.addEventListener('mousedown', outside))
onBeforeUnmount(() => document.removeEventListener('mousedown', outside))
</script>

<template>
  <div ref="root" class="ss" :class="{ open, disabled }" @click="toggle">
    <div ref="control" class="ss-control">
      <div class="ss-value">
        <template v-if="open">
          <input ref="search" v-model="query" class="ss-input" :placeholder="placeholder" @keydown="onKeydown" @click.stop />
        </template>
        <template v-else>
          <span v-if="selectedLabel" class="ss-selected">{{ selectedLabel }}</span>
          <span v-else class="ss-placeholder">{{ placeholder }}</span>
        </template>
      </div>
      <button v-if="clearable && selectedLabel && !disabled" class="ss-clear" type="button" @click.stop="clear">×</button>
      <span class="ss-arrow">⌄</span>
    </div>
    <div v-if="open" class="ss-drop" @click.stop>
      <div v-if="!filtered.length" class="ss-empty">没有匹配项</div>
      <button v-for="(o, i) in filtered" :key="valueOf(o)" type="button" class="ss-option" :class="{ active: i === active, selected: selectedValues.some(v => String(v) === String(valueOf(o))) }" @mouseenter="active = i" @click="choose(o)">
        <span class="ss-option-label">{{ labelOf(o) }}</span>
        <span v-if="subOf(o)" class="ss-option-sub">{{ subOf(o) }}</span>
        <span v-if="selectedValues.some(v => String(v) === String(valueOf(o)))" class="ss-check">✓</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.ss { position: relative; width: 100%; font-size: 13px; }
.ss-control { display: flex; align-items: center; min-height: 34px; padding: 0 8px; border: 1px solid var(--line-strong); border-radius: 6px; background: var(--panel); cursor: pointer; }
.ss.open .ss-control { border-color: var(--brand); box-shadow: 0 0 0 2px rgba(24,144,255,.12); }
.ss.disabled { opacity: .55; pointer-events: none; }
.ss-value { flex: 1; min-width: 0; overflow: hidden; }
.ss-selected { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--ink); }
.ss-placeholder { color: var(--muted); }
.ss-input { width: 100%; height: 30px; border: 0; outline: 0; background: transparent; color: var(--ink); padding: 0; }
.ss-arrow { color: var(--muted); font-size: 14px; margin-left: 6px; }
.ss-clear { border: 0; background: transparent; color: var(--muted); padding: 0 4px; font-size: 15px; line-height: 1; cursor: pointer; }
.ss-drop { position: absolute; z-index: 80; left: 0; right: 0; top: calc(100% + 4px); max-height: 280px; overflow: auto; padding: 4px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.12); }
.ss-option { width: 100%; border: 0; background: transparent; display: flex; align-items: center; gap: 8px; min-height: 34px; padding: 6px 8px; border-radius: 5px; text-align: left; color: var(--regular); cursor: pointer; }
.ss-option.active, .ss-option:hover { background: var(--brand-soft); }
.ss-option.selected { color: var(--brand); }
.ss-option-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ss-option-sub { color: var(--muted); font-size: 11px; white-space: nowrap; }
.ss-check { color: var(--brand); font-weight: 700; }
.ss-empty { padding: 12px; color: var(--muted); text-align: center; font-size: 12px; }
</style>
'''
io.open(p,'w',encoding='utf-8',newline='').write(content)
print('search select')
