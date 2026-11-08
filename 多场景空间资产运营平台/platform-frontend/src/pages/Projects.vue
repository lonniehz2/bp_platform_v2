<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'
import Pager from '../components/Pager.vue'

const projects = ref([])
const templates = ref([])
const modes = ref([])
const page = ref(1)
const error = ref('')
const busy = ref(false)
const pagedProjects = computed(() => projects.value.slice((page.value - 1) * 10, page.value * 10))
const form = reactive({ orgCode: '', orgName: '保障房项目', businessMode: 'PUBLIC_RENTAL', spaceTemplateId: '', defaultAssetTypeCode: 'PUBLIC_RENTAL' })

async function load() {
  try {
    const [p, t, m] = await Promise.all([
      api.projects(), api.templates('GUARANTEE'), api.modes('GUARANTEE')
    ])
    projects.value = p
    templates.value = t
    modes.value = m
    if (!form.spaceTemplateId && t.length) form.spaceTemplateId = t[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true
  error.value = ''
  try {
    if (!form.orgCode.trim()) throw new Error('请填写项目编码')
    await api.createProject({
      orgCode: form.orgCode.trim(),
      orgName: form.orgName.trim(),
      sceneCode: 'GUARANTEE',
      businessMode: form.businessMode,
      spaceTemplateId: form.spaceTemplateId,
      defaultAssetTypeCode: form.defaultAssetTypeCode
    })
    form.orgCode = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function selectProject(p) {
  localStorage.setItem('platformProjectId', p.id)
  error.value = ''
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head">
        <div><h2>项目与空间模板</h2><p>保障房项目选择空间模板，创建后进入资产和业务页面</p></div>
        <span class="pill">GUARANTEE</span>
      </div>
      <div class="row">
        <div class="field"><label>项目编码</label><input v-model="form.orgCode" placeholder="如 GUA_001" /></div>
        <div class="field"><label>项目名称</label><input v-model="form.orgName" /></div>
        <div class="field"><label>经营模式</label>
          <select v-model="form.businessMode">
            <option v-for="m in modes" :key="m.modeCode" :value="m.modeCode">{{ m.modeName }}</option>
          </select>
        </div>
        <div class="field"><label>空间模板</label>
          <select v-model="form.spaceTemplateId">
            <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.templateName }}（{{ t.baseLevelCount }}级）</option>
          </select>
        </div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">创建项目</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>项目列表</h2><span class="small muted">点击项目切换当前上下文</span></div>
      <div v-if="!projects.length" class="empty">暂无项目</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>项目编码</th><th>项目名称</th><th>场景</th><th>经营模式</th><th>空间模板</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="p in pagedProjects" :key="p.id">
              <td class="mono">{{ p.orgCode }}</td>
              <td>{{ p.orgName }}</td>
              <td><span class="badge blue">{{ p.sceneCode }}</span></td>
              <td>{{ p.businessMode }}</td>
              <td>{{ p.templateName || p.spaceTemplateId }}</td>
              <td><span class="badge green">{{ p.status }}</span></td>
              <td><button class="sm" @click="selectProject(p)">设为当前</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pager :total="projects.length" :page="page" @update:page="page = $event" />
    </div>
  </div>
</template>
