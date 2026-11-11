<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  rows: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] },
  rowKey: { type: String, default: 'id' },
  loading: { type: Boolean, default: false },
  selectable: { type: Boolean, default: false },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 },
  total: { type: Number, default: 0 },
  emptyText: { type: String, default: '' },
  density: { type: String, default: 'normal' },
  rowClass: { type: Function, default: null }
})
const emit = defineEmits(['update:page', 'update:pageSize', 'selectionChange', 'sortChange', 'rowClick'])
const selected = ref(new Set())
const pageCount = computed(() => Math.max(1, Math.ceil((props.total || props.rows.length) / props.pageSize)))
const allChecked = computed(() => props.rows.length > 0 && props.rows.every(r => selected.value.has(String(r[props.rowKey]))))
const someChecked = computed(() => props.rows.some(r => selected.value.has(String(r[props.rowKey]))))

watch(() => props.rows, () => {
  const valid = new Set(props.rows.map(r => String(r[props.rowKey])))
  selected.value = new Set([...selected.value].filter(k => valid.has(k)))
})

function toggleAll(e) {
  const next = new Set(selected.value)
  if (e.target.checked) props.rows.forEach(r => next.add(String(r[props.rowKey])))
  else props.rows.forEach(r => next.delete(String(r[props.rowKey])))
  selected.value = next
  emit('selectionChange', props.rows.filter(r => next.has(String(r[props.rowKey]))))
}
function toggleRow(row) {
  const key = String(row[props.rowKey])
  const next = new Set(selected.value)
  next.has(key) ? next.delete(key) : next.add(key)
  selected.value = next
  emit('selectionChange', props.rows.filter(r => next.has(String(r[props.rowKey]))))
}
function cell(row, col) {
  if (col.formatter) return col.formatter(row)
  const v = row[col.key]
  return v === null || v === undefined || v === '' ? '-' : v
}
function sort(col) {
  if (!col.sortable) return
  emit('sortChange', col.key)
}
function go(p) {
  if (p < 1 || p > pageCount.value || p === props.page) return
  emit('update:page', p)
}
function setSize(e) {
  emit('update:pageSize', Number(e.target.value))
  emit('update:page', 1)
}
</script>

<template>
  <div class="dt" :class="'dt-' + density">
    <div class="dt-wrap">
      <table>
        <thead>
          <tr>
            <th v-if="selectable" class="dt-check"><input type="checkbox" :checked="allChecked" :indeterminate.prop="someChecked && !allChecked" @change="toggleAll" /></th>
            <th v-for="c in columns" :key="c.key" :style="{ width: c.width, textAlign: c.align || 'left' }" :class="{ sortable: c.sortable }" @click="sort(c)">
              {{ c.title }}<span v-if="c.sortable" class="dt-sort">↕</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td :colspan="columns.length + (selectable ? 1 : 0)" class="dt-state">{{ t('components.loading') }}</td></tr>
          <tr v-else-if="!rows.length"><td :colspan="columns.length + (selectable ? 1 : 0)" class="dt-state">{{ emptyText || t('components.noData') }}</td></tr>
          <template v-else>
            <tr v-for="row in rows" :key="row[rowKey]" :class="rowClass ? rowClass(row) : ''" @click="$emit('rowClick', row)">
              <td v-if="selectable" class="dt-check" @click.stop><input type="checkbox" :checked="selected.has(String(row[rowKey]))" @change="toggleRow(row)" /></td>
              <td v-for="c in columns" :key="c.key" :style="{ textAlign: c.align || 'left' }">
                <slot :name="'cell-' + c.key" :row="row" :value="row[c.key]">{{ cell(row, c) }}</slot>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <div v-if="total > pageSize || total === 0" class="dt-foot">
      <span class="dt-total">{{ t('components.total') }} {{ total }} {{ t('components.records') }}</span>
      <select :value="pageSize" class="dt-size" @change="setSize">
        <option :value="10">{{ 10 }} {{ t('components.perPage') }}</option>
        <option :value="20">{{ 20 }} {{ t('components.perPage') }}</option>
        <option :value="50">{{ 50 }} {{ t('components.perPage') }}</option>
      </select>
      <button class="sm" :disabled="page <= 1" @click="go(page - 1)">{{ t('components.prev') }}</button>
      <span class="dt-page">{{ page }} / {{ pageCount }}</span>
      <button class="sm" :disabled="page >= pageCount" @click="go(page + 1)">{{ t('components.next') }}</button>
    </div>
  </div>
</template>

<style scoped>
.dt { width: 100%; }
.dt-wrap { overflow: auto; border: 1px solid var(--line); border-radius: 6px; background: var(--panel); }
table { width: 100%; border-collapse: collapse; }
th { background: var(--bg); color: var(--muted); font-size: 12px; font-weight: 500; text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--line); white-space: nowrap; }
th.sortable { cursor: pointer; user-select: none; }
.dt-sort { margin-left: 4px; color: var(--muted); font-size: 10px; }
td { padding: 11px 12px; border-bottom: 1px solid var(--line); color: var(--regular); font-size: 13px; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover td { background: var(--brand-soft); }
.dt-compact td { padding: 7px 10px; }
.dt-compact th { padding: 7px 10px; }
.dt-check { width: 38px; text-align: center; }
.dt-state { text-align: center; color: var(--muted); padding: 32px 12px !important; }
.dt-foot { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding-top: 10px; color: var(--muted); font-size: 12px; }
.dt-size { height: 30px; border: 1px solid var(--line); border-radius: 5px; background: var(--panel); color: var(--regular); }
.dt-page { min-width: 54px; text-align: center; }
</style>
