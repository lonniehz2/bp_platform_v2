<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import TreeSelect from '../components/TreeSelect.vue'
import { can } from '../permissions'
import Pager from '../components/Pager.vue'

const projects = ref([])
const templates = ref([])
const modes = ref([])
const spaces = ref([])
const houses = ref([])
const assetTypes = ref([])
const currentProject = ref(null)
const page = ref(1)
const error = ref('')
const busy = ref(false)
const pagedProjects = computed(() => projects.value.slice((page.value - 1) * 10, page.value * 10))
const form = reactive({ orgCode: '', orgName: '保障房项目', businessMode: 'PUBLIC_RENTAL', spaceTemplateId: '', defaultAssetTypeCode: 'PUBLIC_RENTAL', address: '', contactName: '', contactPhone: '', remark: '', totalArea: 0, landArea: 0, propertyType: '', buildYear: 2020 })
const spaceForm = reactive({ parentId: '', spaceCode: '', spaceName: '', spaceType: 'BUILDING', assetTypeCode: 'PUBLIC_RENTAL', rentable: false, area: 0 })
const spaceTypes = ['AREA', 'BUILDING', 'UNIT', 'FLOOR', 'ROOM', 'INNER_ROOM', 'BED']

async function load() {
  try {
    const [p, t, m, at] = await Promise.all([
      api.projects(), api.templates('GUARANTEE'), api.modes('GUARANTEE'), api.assetTypes('GUARANTEE')
    ])
    projects.value = p
    templates.value = t
    modes.value = m
    assetTypes.value = at
    if (!form.spaceTemplateId && t.length) form.spaceTemplateId = t[0].id
    const saved = String(localStorage.getItem('platformProjectId') || '')
    const chosen = projects.value.find(x => String(x.id) === saved) || projects.value[0]
    if (chosen) await selectProject(chosen)
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.orgCode.trim()) throw new Error('请填写项目编码')
    if (!form.orgName.trim()) throw new Error('请填写项目名称')
    if (form.contactPhone && !/^1\d{10}$/.test(form.contactPhone)) throw new Error('联系电话需为 11 位手机号')
    if (Number(form.totalArea) < 0 || Number(form.landArea) < 0) throw new Error('面积不能为负数')
    if (form.buildYear && (form.buildYear < 1900 || form.buildYear > 2100)) throw new Error('建成年份需在 1900-2100 之间')
    await api.createProject({
      orgCode: form.orgCode.trim(), orgName: form.orgName.trim(),
      sceneCode: 'GUARANTEE', businessMode: form.businessMode,
      spaceTemplateId: form.spaceTemplateId,
      defaultAssetTypeCode: form.defaultAssetTypeCode,
      address: form.address, contactName: form.contactName,
      contactPhone: form.contactPhone, remark: form.remark,
      totalArea: Number(form.totalArea || 0), landArea: Number(form.landArea || 0),
      propertyType: form.propertyType, buildYear: Number(form.buildYear || 0)
    })
    form.orgCode = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function selectProject(p) {
  currentProject.value = p
  localStorage.setItem('platformProjectId', p.id)
  spaceForm.parentId = ''
  await loadAssets()
}

async function loadAssets() {
  if (!currentProject.value) return
  try {
    const id = currentProject.value.id
    const [s, h] = await Promise.all([api.spaces(id), api.houses(id)])
    spaces.value = s; houses.value = h
  } catch (e) { error.value = e.message }
}

async function createSpace() {
  busy.value = true; error.value = ''
  try {
    if (!spaceForm.spaceCode.trim() || !spaceForm.spaceName.trim()) throw new Error('请填写空间编码和名称')
    await api.createSpace(currentProject.value.id, {
      parentId: spaceForm.parentId || null,
      spaceCode: spaceForm.spaceCode.trim(),
      spaceName: spaceForm.spaceName.trim(),
      spaceType: spaceForm.spaceType,
      assetTypeCode: spaceForm.assetTypeCode,
      rentable: spaceForm.spaceType === 'ROOM' || spaceForm.spaceType === 'INNER_ROOM' || spaceForm.spaceType === 'BED'
        ? spaceForm.rentable : false,
      area: Number(spaceForm.area || 0),
      subUnitMode: null
    })
    spaceForm.spaceCode = ''; spaceForm.spaceName = ''
    await loadAssets()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>

    <div class="panel">
      <div class="panel-head">
        <div><h2>项目与空间模板</h2><p>保障房项目选择空间模板，创建后维护空间和房屋</p></div>
        <span class="badge blue">GUARANTEE</span>
      </div>
      <div class="row">
        <div class="field"><label>项目编码</label><input v-model="form.orgCode" placeholder="如 GUA_001" /></div>
        <div class="field"><label>项目名称</label><input v-model="form.orgName" /></div>
        <div class="field"><label>经营模式</label>
          <select v-model="form.businessMode"><option v-for="m in modes" :key="m.modeCode" :value="m.modeCode">{{ m.modeName }}</option></select>
        </div>
        <div class="field"><label>空间模板</label>
          <select v-model="form.spaceTemplateId"><option v-for="t in templates" :key="t.id" :value="t.id">{{ t.templateName }}</option></select>
        </div>
        <div class="field" style="flex:2"><label>项目地址</label><input v-model="form.address" /></div>
        <div class="field"><label>联系人</label><input v-model="form.contactName" /></div>
        <div class="field"><label>联系电话</label><input v-model="form.contactPhone" /></div>
        <div class="field"><label>总建筑面积</label><input v-model.number="form.totalArea" type="number" /></div>
        <div class="field"><label>占地面积</label><input v-model.number="form.landArea" type="number" /></div>
        <div class="field"><label>产权类型</label><select v-model="form.propertyType"><option value="">未填写</option><option value="STATE">国有</option><option value="COLLECTIVE">集体</option><option value="PRIVATE">私有</option></select></div>
        <div class="field"><label>建成年份</label><input v-model.number="form.buildYear" type="number" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">创建项目</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>项目列表</h2><span class="small muted">点击项目切换当前上下文</span></div>
      <div v-if="!projects.length" class="empty">暂无项目</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>项目编码</th><th>项目名称</th><th>地址</th><th>联系人</th><th>总建筑面积</th><th>产权类型</th><th>经营模式</th><th>模板</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="p in pagedProjects" :key="p.id" :class="{ active: currentProject && String(currentProject.id) === String(p.id) }">
              <td class="mono">{{ p.orgCode }}</td><td>{{ p.orgName }}</td><td>{{ p.address || '-' }}</td>
              <td>{{ p.contactName || '-' }} {{ p.contactPhone || '' }}</td><td>{{ p.totalArea || '-' }}</td>
              <td>{{ p.propertyType || '-' }}</td><td>{{ p.businessMode }}</td>
              <td>{{ p.templateName || p.spaceTemplateId }}</td>
              <td><span class="badge green">{{ p.status }}</span></td>
              <td><button class="sm" @click="selectProject(p)">设为当前</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pager :total="projects.length" :page="page" @update:page="page = $event" />
    </div>

    <template v-if="currentProject">
      <div class="panel">
        <div class="panel-head">
          <div><h2>空间树</h2><p>{{ currentProject.orgName }} · 小区/楼栋/单元/楼层/房屋/内房/床位</p></div>
          <span class="small muted">{{ spaces.length }} 个空间 · {{ houses.length }} 个房源</span>
        </div>
        <div class="row" style="margin-bottom:12px">
          <div class="field"><label>上级空间</label>
            <TreeSelect v-model="spaceForm.parentId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" placeholder="选择上级空间（空为根）" clearable />
          </div>
          <div class="field"><label>空间编码</label><input v-model="spaceForm.spaceCode" placeholder="如 A / 101" /></div>
          <div class="field"><label>空间名称</label><input v-model="spaceForm.spaceName" placeholder="如 A栋 / 101室" /></div>
          <div class="field"><label>类型</label>
            <select v-model="spaceForm.spaceType"><option v-for="t in spaceTypes" :key="t" :value="t">{{ t }}</option></select>
          </div>
          <div class="field"><label>资产类型</label>
            <select v-model="spaceForm.assetTypeCode"><option v-for="t in assetTypes" :key="t.typeCode" :value="t.typeCode">{{ t.typeName }}</option></select>
          </div>
          <div class="field" v-if="['ROOM','INNER_ROOM','BED'].includes(spaceForm.spaceType)" style="flex:0 0 auto">
            <label>可出租</label><input v-model="spaceForm.rentable" type="checkbox" style="width:auto" />
          </div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="createSpace">新增空间</button></div>
        </div>
        <div v-if="!spaces.length" class="empty">暂无空间</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>空间编码</th><th>名称</th><th>类型</th><th>层级</th><th>资产类型</th><th>路径</th></tr></thead>
            <tbody>
              <tr v-for="s in spaces" :key="s.id">
                <td class="mono">{{ s.spaceCode }}</td><td>{{ s.spaceName }}</td><td>{{ s.spaceType }}</td>
                <td>{{ s.levelNo }}</td><td>{{ s.assetTypeCode || '-' }}</td><td class="small">{{ s.spacePath }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>房屋/房源</h2><span class="small muted">可出租空间自动生成房源</span></div>
        <div v-if="!houses.length" class="empty">暂无房源</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>房源编码</th><th>名称</th><th>资产类型</th><th>面积</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="h in houses" :key="h.id">
                <td class="mono">{{ h.houseCode }}</td><td>{{ h.houseName }}</td>
                <td>{{ h.assetTypeCode || '-' }}</td><td>{{ h.area || '-' }}</td>
                <td><span class="badge" :class="h.houseStatus === 'VACANT' ? 'green' : 'orange'">{{ h.houseStatus }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
