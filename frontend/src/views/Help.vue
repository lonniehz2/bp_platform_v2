<template>
  <div class="page-card help-page">
    <div class="toolbar help-toolbar">
      <h3 style="margin:0">使用帮助</h3>
      <el-tag size="small" type="info">{{ HELP_VERSION }}</el-tag>
      <span v-if="keyword" class="result-count">命中 {{ filtered.length }} 章</span>
      <div class="spacer" />
      <el-select v-if="isMobile" v-model="active" class="mobile-toc-select"
                 size="small" @change="jump">
        <el-option v-for="s in filtered" :key="s.id" :label="s.title" :value="s.id" />
      </el-select>
      <el-input v-model="keyword" class="search-input"
                placeholder="搜索操作，如「核销」「退租」" clearable />
      <el-button size="small" @click="downloadPdf">下载 PDF 版</el-button>
      <el-button size="small" type="primary" @click="printDoc">打印 / 另存 PDF</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :sm="24" :md="6" :lg="6" class="toc-col">
        <div class="toc">
          <template v-for="s in filtered" :key="s.id">
            <div :class="['toc-item', { active: active === s.id }]"
                 @click="jump(s.id)">
              {{ s.title }}
            </div>
            <div v-for="sub in subsOf(s.id)" v-if="active === s.id"
                 :key="sub.id" :class="['toc-sub', { active: activeSub === sub.id }]"
                 @click="jumpSub(s.id, sub.bidx)">
              {{ sub.text }}
            </div>
          </template>
          <el-empty v-if="!filtered.length" description="没有匹配的章节" :image-size="60" />
        </div>
      </el-col>

      <el-col :xs="24" :sm="24" :md="18" :lg="18">
        <div ref="bodyRef" class="help-body" @scroll="onScroll">
          <section v-for="s in filtered" :key="s.id" :id="'sec-' + s.id" class="sec">
            <h2>{{ s.title }}</h2>
            <template v-for="(b, i) in s.blocks" :key="i">
              <h3 v-if="b.type === 'h3'" :id="'sub-' + s.id + '-' + i">
                <span v-html="mark(b.text)" />
              </h3>
              <p v-else-if="b.type === 'p'" v-html="mark(b.text)" />
              <ol v-else-if="b.type === 'ol'" class="steps">
                <li v-for="(it, j) in b.items" :key="j" v-html="mark(it)" />
              </ol>
              <ul v-else-if="b.type === 'ul'" class="bullets">
                <li v-for="(it, j) in b.items" :key="j" v-html="mark(it)" />
              </ul>
              <el-alert v-else-if="b.type === 'note'" type="info" :closable="false"
                        show-icon class="note">
                <span v-html="mark(b.text)" />
              </el-alert>
              <div v-else-if="b.type === 'table'" class="table-wrap">
                <el-table :data="b.rows" border size="small" class="tbl">
                  <el-table-column v-for="(h, k) in b.head" :key="k"
                                   :label="h" :min-width="k === 0 ? 160 : 220">
                    <template #default="{ row }">
                      <span v-html="mark(row[k])" />
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <pre v-else-if="b.type === 'code'" class="formula" v-html="mark(b.text)" />
              <el-collapse v-else-if="b.type === 'faq'" class="faq">
                <el-collapse-item v-for="(f, j) in b.items" :key="j" :name="j">
                  <template #title>
                    <span v-html="mark(f.q)" />
                  </template>
                  <p class="faq-a" v-html="mark(f.a)" />
                </el-collapse-item>
              </el-collapse>
              <el-image v-else-if="b.type === 'image'" :src="b.src" fit="contain"
                        :preview-src-list="[b.src]" class="help-img" />
            </template>
          </section>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/**
 * 内置使用帮助：内容来自 content/help.js。
 * P2：二级目录、滚动定位、搜索高亮、移动端适配。
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { HELP_SECTIONS, HELP_VERSION, HELP_PDF, sectionForRoute } from '@/content/help'

const route = useRoute()

const keyword = ref('')
const bodyRef = ref(null)
const isMobile = ref(false)
const activeSub = ref('')

const initial = String(route.query.sec || '') || sectionForRoute(route.path)
const active = ref(HELP_SECTIONS.some((x) => x.id === initial)
  ? initial : (HELP_SECTIONS[0]?.id || ''))

const filtered = computed(() => {
  const k = keyword.value.trim()
  if (!k) return HELP_SECTIONS
  return HELP_SECTIONS.filter((s) => JSON.stringify(s).includes(k))
})

// 二级目录：章节内 h3，保留 block 下标用于锚点
const subsMap = computed(() => {
  const map = {}
  for (const s of HELP_SECTIONS) {
    map[s.id] = s.blocks
      .map((b, i) => (b.type === 'h3' ? { id: `sub-${s.id}-${i}`, text: b.text, bidx: i } : null))
      .filter(Boolean)
  }
  return map
})

function subsOf(id) {
  return subsMap.value[id] || []
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function mark(text) {
  const html = escapeHtml(text)
  const k = keyword.value.trim()
  if (!k) return html
  const pattern = k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return html.replace(new RegExp(`(${pattern})`, 'gi'), '<mark>$1</mark>')
}

function jump(id) {
  active.value = id
  activeSub.value = ''
  const el = document.getElementById('sec-' + id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function jumpSub(sid, bidx) {
  active.value = sid
  const subId = `sub-${sid}-${bidx}`
  activeSub.value = subId
  const el = document.getElementById(subId)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// 滚动时同步高亮当前章节 / 小节
function onScroll() {
  const body = bodyRef.value
  if (!body) return
  const bodyTop = body.getBoundingClientRect().top
  let current = filtered.value[0]
  for (const s of filtered.value) {
    const el = document.getElementById('sec-' + s.id)
    if (el && el.getBoundingClientRect().top - bodyTop <= 36) current = s
  }
  if (current && current.id !== active.value) {
    active.value = current.id
    activeSub.value = ''
  }
  const subs = subsOf(active.value)
  let curSub = ''
  for (const sub of subs) {
    const el = document.getElementById(sub.id)
    if (el && el.getBoundingClientRect().top - bodyTop <= 70) curSub = sub.id
  }
  if (activeSub.value !== curSub) activeSub.value = curSub
}

let scrollTick = false
function throttledScroll() {
  if (scrollTick) return
  scrollTick = true
  requestAnimationFrame(() => {
    scrollTick = false
    onScroll()
  })
}

function resize() {
  isMobile.value = window.innerWidth < 768
  document.documentElement.classList.toggle('help-open-mobile', isMobile.value)
  document.body.classList.toggle('help-open-mobile', isMobile.value)
}

onMounted(() => {
  resize()
  window.addEventListener('resize', resize)
  if (initial && initial !== HELP_SECTIONS[0]?.id) {
    setTimeout(() => jump(initial), 120)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  document.documentElement.classList.remove('help-open-mobile')
  document.body.classList.remove('help-open-mobile')
})

watch(keyword, () => {
  if (filtered.value.length && !filtered.value.some((s) => s.id === active.value)) {
    active.value = filtered.value[0].id
    activeSub.value = ''
  }
  nextTick(throttledScroll)
})

watch(() => route.query.sec, (sec) => {
  if (sec && sec !== active.value) jump(String(sec))
})

function downloadPdf() {
  window.open(HELP_PDF, '_blank')
}

function printDoc() {
  window.print()
}
</script>

<style scoped>
.help-page { min-height: 78vh; }
.help-toolbar { flex-wrap: wrap; gap: 8px; }
.result-count { font-size: 12px; color: var(--el-text-color-secondary); }
.search-input { width: 240px; }
.mobile-toc-select { display: none; }
.toc {
  position: sticky;
  top: 8px;
  border-right: 1px solid var(--el-border-color-light);
  padding-right: 12px;
  max-height: 76vh;
  overflow: auto;
}
.toc-item {
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--el-text-color-primary);
}
.toc-item:hover { background: var(--el-fill-color-light); }
.toc-item.active { background: var(--el-color-primary-light-9); color: var(--el-color-primary); font-weight: 600; }
.toc-sub {
  padding: 4px 10px 4px 24px;
  margin: 1px 0;
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}
.toc-sub:hover { background: var(--el-fill-color-light); color: var(--el-text-color-primary); }
.toc-sub.active { color: var(--el-color-primary); background: var(--el-color-primary-light-9); }
.help-body { max-height: 76vh; overflow: auto; padding-right: 8px; }
.sec { margin-bottom: 26px; }
.sec h2 {
  font-size: 17px;
  margin: 6px 0 10px;
  padding-left: 8px;
  border-left: 3px solid var(--el-color-primary);
  scroll-margin-top: 8px;
}
.sec h3 { font-size: 14px; margin: 14px 0 6px; color: var(--el-text-color-primary); scroll-margin-top: 8px; }
.sec p { margin: 6px 0; line-height: 1.8; color: var(--el-text-color-regular); font-size: 13px; }
.steps, .bullets { margin: 6px 0 6px 20px; font-size: 13px; line-height: 1.9; color: var(--el-text-color-regular); }
.note { margin: 8px 0; }
.tbl { margin: 8px 0 4px; }
.table-wrap { width: 100%; max-width: 100%; overflow-x: auto; margin: 8px 0 4px; }
.table-wrap .tbl { margin: 0; width: 100%; }
.formula {
  margin: 10px 0; padding: 10px 12px; border-radius: 6px;
  background: var(--el-fill-color-light); border: 1px solid var(--el-border-color-light);
  font-family: Consolas, 'Courier New', monospace; font-size: 12px; line-height: 1.7;
  white-space: pre-wrap; overflow-x: auto; color: var(--el-text-color-primary);
}
.faq { margin: 10px 0; }
.faq-a { line-height: 1.8; color: var(--el-text-color-regular); font-size: 13px; }
.help-img { max-width: 100%; margin: 10px 0; border: 1px solid var(--el-border-color-light); }
:deep(mark) {
  background: #ffe58f;
  color: #333;
  padding: 0 1px;
  border-radius: 2px;
}
:global(html.help-open-mobile),
:global(body.help-open-mobile) { overflow: hidden; }

@media (max-width: 767px) {
  /* 手机端帮助页全屏展示，避免被左侧主菜单挤压 */
  .help-page {
    position: fixed;
    inset: 0;
    z-index: 3000;
    margin: 0;
    padding: 10px 12px 16px;
    border-radius: 0;
    overflow: auto;
    background: var(--el-bg-color-page);
  }
  .help-toolbar {
    position: sticky;
    top: 0;
    z-index: 5;
    align-items: center;
    padding-bottom: 6px;
    background: var(--el-bg-color-page);
  }
  .help-toolbar h3 { font-size: 15px; width: 100%; }
  .help-toolbar .spacer { display: none; }
  .mobile-toc-select { display: block; order: 3; flex: 1 1 100%; width: 100%; }
  .search-input { order: 4; width: 100%; }
  .help-toolbar .el-button { flex: 1; margin-left: 0; }
  .toc-col { display: none; }
  .help-page :deep(.el-row) { margin-left: 0 !important; margin-right: 0 !important; }
  .help-page :deep(.el-col) { padding-left: 0 !important; padding-right: 0 !important; }
  .help-body { max-height: calc(100vh - 220px); padding-right: 0; }
  .sec h2 { font-size: 16px; }
  .formula { font-size: 11px; }
  .tbl { width: 100%; }
  .tbl :deep(.el-table) { width: 100% !important; }
}

@media print {
  .toolbar, .toc, .toc-col, .mobile-toc-select { display: none; }
  .help-body { max-height: none; overflow: visible; }
  .el-col-18 { width: 100%; max-width: 100%; flex: 0 0 100%; }
}
</style>
