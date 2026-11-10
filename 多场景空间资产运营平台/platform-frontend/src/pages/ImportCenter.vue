<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api'

const personFile = ref(null)
const personBusy = ref(false)
const personResult = ref(null)
const personError = ref('')
const spaceFile = ref(null)
const spaceBusy = ref(false)
const spaceResult = ref(null)
const spaceError = ref('')
const relationFile = ref(null)
const relationBusy = ref(false)
const relationResult = ref(null)
const relationError = ref('')
const bindingFile = ref(null)
const bindingBusy = ref(false)
const bindingResult = ref(null)
const bindingError = ref('')

function pickPerson(e) { personFile.value = e.target.files?.[0] || null; personResult.value = null; personError.value = '' }

function pickBinding(e) { bindingFile.value = e.target.files?.[0] || null; bindingResult.value = null; bindingError.value = '' }

function downloadBindingTemplate() {
  const csv = '\ufeff项目编码,设备编码,空间编码\nZZ0020,LOCK-001,101\n'
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = '设备资产绑定导入模板.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importBindings() {
  if (!bindingFile.value) { bindingError.value = '请选择 CSV 文件'; return }
  bindingBusy.value = true; bindingError.value = ''; bindingResult.value = null
  try { bindingResult.value = await api.importDeviceBindings(bindingFile.value) } catch (e) { bindingError.value = e.message } finally { bindingBusy.value = false }
}

function pickRelation(e) { relationFile.value = e.target.files?.[0] || null; relationResult.value = null; relationError.value = '' }

function downloadRelationTemplate() {
  const csv = '\ufeff项目编码,人员编码,房屋编码,关系类型,开始日期,结束日期,是否主要关系\n'
    + 'ZZ0020,P0001,101,TENANT,2026-01-01,2026-12-31,是\n'
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = '人员资产关系导入模板.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importRelations() {
  if (!relationFile.value) { relationError.value = '请选择 CSV 文件'; return }
  relationBusy.value = true; relationError.value = ''; relationResult.value = null
  try { relationResult.value = await api.importPersonAssets(relationFile.value) } catch (e) { relationError.value = e.message } finally { relationBusy.value = false }
}

function pickSpace(e) { spaceFile.value = e.target.files?.[0] || null; spaceResult.value = null; spaceError.value = '' }

function downloadSpaceTemplate() {
  const csv = '\ufeff项目编码,上级空间编码,空间编码,空间名称,空间类型,资产类型,建筑面积,套内面积,可出租\n'
    + 'ZZ0020,A栋,1单元,1单元,UNIT,PUBLIC_RENTAL,0,0,否\n'
    + 'ZZ0020,1单元,101,101室,ROOM,PUBLIC_RENTAL,60,52,是\n'
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = '房屋空间导入模板.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importSpaces() {
  if (!spaceFile.value) { spaceError.value = '请选择 CSV 文件'; return }
  spaceBusy.value = true; spaceError.value = ''; spaceResult.value = null
  try { spaceResult.value = await api.importSpaces(spaceFile.value) } catch (e) { spaceError.value = e.message } finally { spaceBusy.value = false }
}

function downloadPersonTemplate() {
  const csv = '\ufeff人员编码,姓名,手机号,身份证脱敏,人员类型,性别,出生日期,地址,工作单位,紧急联系人,备注\n'
    + 'P0001,张三,13800000000,330***********1234,GUARANTEE_TENANT,MALE,1990-01-01,示例地址,示例单位,李四,导入示例\n'
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = '人员导入模板.csv'; a.click(); URL.revokeObjectURL(a.href)
}

async function importPersons() {
  if (!personFile.value) { personError.value = '请选择 CSV 文件'; return }
  personBusy.value = true; personError.value = ''; personResult.value = null
  try { personResult.value = await api.importPersons(personFile.value) } catch (e) { personError.value = e.message } finally { personBusy.value = false }
}
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head"><div><h2>批量导入</h2><p>基础数据导入入口 · 校验后逐行入库</p></div><span class="pill">IMPORT</span></div>
      <div class="alert">人员导入支持 CSV；设备导入模板同时创建空间、房屋和设备，请到设备绑定页使用。</div>
    </div>

    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="panel">
        <div class="panel-head"><h2>人员导入</h2><span class="small muted">CSV</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadPersonTemplate">下载模板</button><input type="file" accept=".csv" @change="pickPerson" /><span class="small muted">{{ personFile?.name || '未选择文件' }}</span></div>
        <div v-if="personError" class="error">{{ personError }}</div>
        <button class="primary" :disabled="personBusy || !personFile" @click="importPersons">{{ personBusy ? '导入中…' : '开始导入' }}</button>
        <div v-if="personResult" style="margin-top:12px">
          <div class="alert" :class="personResult.failed ? 'warn' : 'ok'">共 {{ personResult.total }} 行，成功 {{ personResult.success }}，失败 {{ personResult.failed }}。</div>
          <div v-if="personResult.errors?.length" class="table-wrap" style="margin-top:8px">
            <table><thead><tr><th>行号</th><th>原因</th></tr></thead><tbody><tr v-for="e in personResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>房屋/空间导入</h2><span class="small muted">CSV</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadSpaceTemplate">下载模板</button><input type="file" accept=".csv" @change="pickSpace" /><span class="small muted">{{ spaceFile?.name || '未选择文件' }}</span></div>
        <div v-if="spaceError" class="error">{{ spaceError }}</div>
        <button class="primary" :disabled="spaceBusy || !spaceFile" @click="importSpaces">{{ spaceBusy ? '导入中…' : '开始导入' }}</button>
        <div v-if="spaceResult" style="margin-top:12px">
          <div class="alert" :class="spaceResult.failed ? 'warn' : 'ok'">共 {{ spaceResult.total }} 行，成功 {{ spaceResult.success }}，失败 {{ spaceResult.failed }}。</div>
          <div v-if="spaceResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>行号</th><th>原因</th></tr></thead><tbody><tr v-for="e in spaceResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>人员-资产关系导入</h2><span class="small muted">CSV</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadRelationTemplate">下载模板</button><input type="file" accept=".csv" @change="pickRelation" /><span class="small muted">{{ relationFile?.name || '未选择文件' }}</span></div>
        <div v-if="relationError" class="error">{{ relationError }}</div>
        <button class="primary" :disabled="relationBusy || !relationFile" @click="importRelations">{{ relationBusy ? '导入中…' : '开始导入' }}</button>
        <div v-if="relationResult" style="margin-top:12px">
          <div class="alert" :class="relationResult.failed ? 'warn' : 'ok'">共 {{ relationResult.total }} 行，成功 {{ relationResult.success }}，失败 {{ relationResult.failed }}。</div>
          <div v-if="relationResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>行号</th><th>原因</th></tr></thead><tbody><tr v-for="e in relationResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>设备-资产绑定导入</h2><span class="small muted">CSV</span></div>
        <div class="row" style="margin-bottom:10px"><button class="sm" @click="downloadBindingTemplate">下载模板</button><input type="file" accept=".csv" @change="pickBinding" /><span class="small muted">{{ bindingFile?.name || '未选择文件' }}</span></div>
        <div v-if="bindingError" class="error">{{ bindingError }}</div>
        <button class="primary" :disabled="bindingBusy || !bindingFile" @click="importBindings">{{ bindingBusy ? '导入中…' : '开始导入' }}</button>
        <div v-if="bindingResult" style="margin-top:12px">
          <div class="alert" :class="bindingResult.failed ? 'warn' : 'ok'">共 {{ bindingResult.total }} 行，成功 {{ bindingResult.success }}，失败 {{ bindingResult.failed }}。</div>
          <div v-if="bindingResult.errors?.length" class="table-wrap" style="margin-top:8px"><table><thead><tr><th>行号</th><th>原因</th></tr></thead><tbody><tr v-for="e in bindingResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody></table></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>设备导入</h2><span class="small muted">CSV</span></div>
        <p class="muted">设备导入模板按“组织-楼栋-单元-楼层-房间-设备”一行一台设备，导入时自动创建空间和房屋。</p>
        <RouterLink class="primary" to="/guarantee/device-bind">去设备绑定页导入</RouterLink>
      </div>
    </div>
  </div>
</template>
