# -*- coding: utf-8 -*-
"""前端：字段字典改为「接口优先 + 静态兜底」，并在 DetailView 中使用"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 字段字典模块：增加运行时字典 ----------
P = os.path.join(FE, 'constants', 'fieldLabels.js')
s = io.open(P, encoding='utf-8').read()

if 'loadRemoteLabels' not in s:
    s = s.rstrip() + '''

/**
 * 运行时字典：来自后端 /sys/field-labels（源数据是 MySQL 列注释）。
 *
 * 静态 FIELD_LABEL 只能覆盖「表格里出现过的字段」，
 * 详情里还会露出 standardId、payMode 这类没在表头出现的字段。
 * 后端列注释 100% 覆盖，因此用它兜底最完整。
 */
const remote = {}

let loading = null

/** 只加载一次；失败则静默回退静态字典 */
export function loadRemoteLabels(api) {
  if (loading) {
    return loading
  }
  loading = (async () => {
    try {
      const data = await api()
      if (data && typeof data === 'object') {
        Object.assign(remote, data)
      }
    } catch (e) {
      // 忽略：静态字典仍可用
    }
    return remote
  })()
  return loading
}

/** 同步取标签：远程 → 静态 → 驼峰兜底（xxxId → xxxID） */
export function labelOf(key) {
  if (remote[key]) return remote[key]
  if (FIELD_LABEL[key]) return FIELD_LABEL[key]
  // 兜底：把 Id 结尾的字段拆成「基础字段名 + ID」
  const m = /^(\\w+?)Id$/.exec(key)
  if (m) {
    const base = remote[m[1]] || FIELD_LABEL[m[1]]
    if (base) return base + 'ID'
  }
  return key
}
'''
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ fieldLabels.js 增加远程字典 + labelOf 兜底')

# ---------- 2) DetailView 使用 labelOf 并触发加载 ----------
D = os.path.join(FE, 'components', 'DetailView.vue')
t = io.open(D, encoding='utf-8').read()
t = t.replace("import { fieldLabel, INTERNAL_FIELDS } from '@/constants/fieldLabels'",
              "import { labelOf, INTERNAL_FIELDS, loadRemoteLabels } from '@/constants/fieldLabels'\n"
              "import { onMounted, ref as vueRef } from 'vue'\n"
              "import request from '@/api/request'")
t = t.replace("import { computed, ref } from 'vue'",
              "import { computed, ref } from 'vue'")

# 用 labelOf 替代 fieldLabel
t = t.replace("  const label = fieldLabel(key)", "  const label = labelOf(key)")

# 触发一次加载，加载完成后强制重算
t = t.replace("const showRaw = ref(false)",
              "const showRaw = ref(false)\nconst labelVersion = ref(0)\n\n"
              "onMounted(async () => {\n"
              "  await loadRemoteLabels(() => request.get('/sys/field-labels'))\n"
              "  labelVersion.value++   // 触发字段标签重算\n"
              "})")

# 让 computed 依赖 labelVersion
t = t.replace("const mainFields = computed(() => {\n  const row = props.row || {}",
              "const mainFields = computed(() => {\n  void labelVersion.value\n  const row = props.row || {}")
t = t.replace("const internalFields = computed(() => {\n  const row = props.row || {}",
              "const internalFields = computed(() => {\n  void labelVersion.value\n  const row = props.row || {}")

io.open(D, 'w', encoding='utf-8').write(t)
print('  ✓ DetailView.vue 接入远程字段字典（加载后自动重算）')
