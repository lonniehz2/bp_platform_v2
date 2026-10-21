# -*- coding: utf-8 -*-
"""重写 Arrears.vue（催缴列表 + 登记催缴 + 扫描生成）"""
import io

P = r'D:\Work\业务平台开发\frontend\src\views\Arrears.vue'

SRC = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">催缴管理</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button type="success" @click="dunningVisible = true">登记催缴</el-button>
      <el-button @click="scan">扫描生成催缴</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="催缴后仍不缴可触发欠费停权；默认只停门锁、不停大门（EXCLUDE_MAIN_DOOR）"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <pre class="raw">{{ JSON.stringify(row, null, 2) }}</pre>
        </template>
      </el-table-column>
      <el-table-column prop="billId" label="账单ID" width="150" />
      <el-table-column prop="personId" label="人员" width="120" />
      <el-table-column prop="actionType" label="催缴方式" width="120" />
      <el-table-column prop="dunningLevel" label="催缴级别" width="120" />
      <el-table-column prop="actionTime" label="时间" width="170" />
      <el-table-column prop="remark" label="备注" min-width="160" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="dunningVisible" title="登记催缴" width="460px">
      <el-form :model="df" label-width="110px">
        <el-form-item label="账单ID"><el-input v-model.number="df.billId" /></el-form-item>
        <el-form-item label="人员ID"><el-input v-model.number="df.personId" /></el-form-item>
        <el-form-item label="催缴方式">
          <el-select v-model="df.actionType" style="width:100%">
            <el-option label="短信" value="SMS" />
            <el-option label="电话" value="CALL" />
            <el-option label="上门" value="VISIT" />
            <el-option label="律师函" value="LETTER" />
          </el-select></el-form-item>
        <el-form-item label="备注">
          <el-input v-model="df.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dunningVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doDunning">确认</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <pre class="raw">{{ JSON.stringify(detail, null, 2) }}</pre>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { financeApi } from '@/api/modules'
import req from '@/api/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
const dunningVisible = ref(false)
const df = reactive({ billId: null, personId: null, actionType: 'SMS', remark: '' })

async function load() {
  loading.value = true
  try {
    const d = await financeApi.arrears({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doDunning() {
  if (!df.billId) { ElMessage.warning('请填写账单ID'); return }
  saving.value = true
  try {
    await req.post('/fin/dunnings', { ...df })
    ElMessage.success('催缴已登记')
    dunningVisible.value = false; load()
  } finally { saving.value = false }
}

async function scan() {
  const r = await financeApi.dunningScan()
  ElMessage.success('扫描完成：生成 ' + (r?.count ?? '若干') + ' 条催缴')
  load()
}

onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
'''

io.open(P, 'w', encoding='utf-8').write(SRC)
print('  ✓ Arrears.vue 整页重写（列表/登记催缴/扫描）')
