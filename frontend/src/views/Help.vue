<template>
  <div class="page-card help-page">
    <div class="toolbar">
      <h3 style="margin:0">使用帮助</h3>
      <el-tag size="small" type="info">{{ HELP_VERSION }}</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="搜索操作，如「核销」「退租」"
                clearable style="width:240px" />
      <el-button type="primary" @click="printDoc">打印 / 另存 PDF</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="6">
        <div class="toc">
          <div v-for="s in filtered" :key="s.id"
               :class="['toc-item', { active: active === s.id }]"
               @click="jump(s.id)">
            {{ s.title }}
          </div>
          <el-empty v-if="!filtered.length" description="没有匹配的章节" :image-size="60" />
        </div>
      </el-col>

      <el-col :span="18">
        <div ref="bodyRef" class="help-body">
          <section v-for="s in filtered" :key="s.id" :id="'sec-' + s.id" class="sec">
            <h2>{{ s.title }}</h2>
            <template v-for="(b, i) in s.blocks" :key="i">
              <h3 v-if="b.type === 'h3'">{{ b.text }}</h3>
              <p v-else-if="b.type === 'p'">{{ b.text }}</p>
              <ol v-else-if="b.type === 'ol'" class="steps">
                <li v-for="(it, j) in b.items" :key="j">{{ it }}</li>
              </ol>
              <ul v-else-if="b.type === 'ul'" class="bullets">
                <li v-for="(it, j) in b.items" :key="j">{{ it }}</li>
              </ul>
              <el-alert v-else-if="b.type === 'note'" type="info" :closable="false"
                        show-icon :title="b.text" class="note" />
              <el-table v-else-if="b.type === 'table'" :data="b.rows" border size="small"
                        class="tbl">
                <el-table-column v-for="(h, k) in b.head" :key="k"
                                 :label="h" :min-width="k === 0 ? 160 : 220">
                  <template #default="{ row }">{{ row[k] }}</template>
                </el-table-column>
              </el-table>
            </template>
          </section>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/**
 * 内置使用帮助：内容来自 content/help.js，左侧目录 + 右侧正文，支持搜索与打印。
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { HELP_SECTIONS, HELP_VERSION } from '@/content/help'

const route = useRoute()

const keyword = ref('')
const sec0 = String(route.query.sec || '')
const active = ref(HELP_SECTIONS.some((x) => x.id === sec0)
  ? sec0 : (HELP_SECTIONS[0]?.id || ''))

// 顶部问号会带 ?sec=xxx：进入后自动滚到对应章节
onMounted(() => {
  if (sec0) setTimeout(() => jump(sec0), 120)
})

const filtered = computed(() => {
  const k = keyword.value.trim()
  if (!k) return HELP_SECTIONS
  return HELP_SECTIONS.filter((s) => {
    const text = JSON.stringify(s)
    return text.includes(k)
  })
})

function jump(id) {
  active.value = id
  const el = document.getElementById('sec-' + id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function printDoc() {
  window.print()
}
</script>

<style scoped>
.help-page { min-height: 78vh; }
.toc {
  position: sticky;
  top: 8px;
  border-right: 1px solid #ebeef5;
  padding-right: 12px;
  max-height: 76vh;
  overflow: auto;
}
.toc-item {
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #303133;
}
.toc-item:hover { background: #f5f7fa; }
.toc-item.active { background: #ecf5ff; color: #409eff; font-weight: 600; }
.help-body { max-height: 76vh; overflow: auto; padding-right: 8px; }
.sec { margin-bottom: 26px; }
.sec h2 {
  font-size: 17px;
  margin: 6px 0 10px;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}
.sec h3 { font-size: 14px; margin: 14px 0 6px; color: #303133; }
.sec p { margin: 6px 0; line-height: 1.8; color: #444; font-size: 13px; }
.steps, .bullets { margin: 6px 0 6px 20px; font-size: 13px; line-height: 1.9; color: #444; }
.note { margin: 8px 0; }
.tbl { margin: 8px 0 4px; }

@media print {
  .toolbar, .toc { display: none; }
  .help-body { max-height: none; overflow: visible; }
  .el-col-18 { width: 100%; max-width: 100%; flex: 0 0 100%; }
}
</style>
