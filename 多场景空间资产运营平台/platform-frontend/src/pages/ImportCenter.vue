<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api'

const personFile = ref(null)
const personBusy = ref(false)
const personResult = ref(null)
const personError = ref('')

function pickPerson(e) { personFile.value = e.target.files?.[0] || null; personResult.value = null; personError.value = '' }

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
        <div class="panel-head"><h2>房屋/空间/设备导入</h2><span class="small muted">CSV</span></div>
        <p class="muted">设备导入模板按“组织-楼栋-单元-楼层-房间-设备”一行一台设备，导入时自动创建空间和房屋。</p>
        <RouterLink class="primary" to="/guarantee/device-bind">去设备绑定页导入</RouterLink>
      </div>
    </div>
  </div>
</template>
