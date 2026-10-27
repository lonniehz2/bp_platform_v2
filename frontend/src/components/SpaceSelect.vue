<template>
  <!-- 空间选择：按空间名称搜索（房间/床位），值为空间 ID -->
  <el-select
    :model-value="modelValue"
    filterable
    clearable
    :loading="loading"
    :placeholder="placeholder"
    :style="{ width: width }"
    :data-testid="testid"
    @update:model-value="(v) => emit('update:modelValue', v)"
  >
    <el-option v-for="x in options" :key="x.id" :label="labelOf(x)" :value="String(x.id)" />
  </el-select>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import req from '@/api/request'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  orgId: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '输入空间名称搜索' },
  width: { type: String, default: '100%' },
  testid: { type: String, default: 'space-select' }
})
const emit = defineEmits(['update:modelValue'])

const options = ref([])
const loading = ref(false)

function flatten(nodes, out) {
  for (const n of nodes || []) {
    out.push(n)
    if (n.children && n.children.length) flatten(n.children, out)
  }
}

function labelOf(x) {
  return (x.spaceName || x.spaceCode || x.id) + (x.spaceType ? ' · ' + x.spaceType : '')
}

async function load() {
  loading.value = true
  try {
    let orgId = props.orgId
    if (!orgId) {
      const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 1 } })
      const first = (d.rows || [])[0]
      orgId = first && first.id
    }
    if (!orgId) { options.value = []; return }
    const tree = await req.get('/spaces/tree', { params: { orgId } })
    const flat = []
    flatten(tree || [], flat)
    options.value = flat.filter((x) => ['ROOM', 'BED'].includes(x.spaceType))
  } catch (e) { options.value = [] } finally { loading.value = false }
}

onMounted(load)
watch(() => props.orgId, load)
</script>
