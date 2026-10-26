# -*- coding: utf-8 -*-
"""P2-4 补贴管理：增加「补贴标准」区块（列表 / 新建 / 启停）。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'Subsidies.vue')
s = io.open(P, encoding='utf-8').read()

TPL = """
    <!-- ==================== 补贴标准 ==================== -->
    <div class="page-card">
      <div class="toolbar">
        <h4 style="margin:0">补贴标准</h4>
        <el-tag size="small" type="info">按保障类型 + 补贴方式配置，停用后不再参与发放</el-tag>
        <div class="spacer" />
        <el-select v-model="stQuery.securityType" placeholder="保障类型" clearable
                   style="width:130px" @change="loadStandards">
          <el-option label="公租房" value="PUBLIC" />
          <el-option label="保障性租赁住房" value="AFFORDABLE" />
          <el-option label="人才公寓" value="TALENT" />
          <el-option label="廉租房" value="LOW_RENT" />
        </el-select>
        <el-select v-model="stQuery.subsidyMode" placeholder="补贴方式" clearable
                   style="width:140px" @change="loadStandards">
          <el-option label="定额" value="FIXED" />
          <el-option label="按面积" value="BY_AREA" />
          <el-option label="按人" value="BY_PERSON" />
          <el-option label="按租金比例" value="RATIO" />
        </el-select>
        <el-input v-model="stQuery.keyword" placeholder="编码/名称" clearable
                  style="width:160px" @keyup.enter="loadStandards" />
        <el-button type="primary" @click="loadStandards">查询</el-button>
        <el-button type="success" @click="openStandard">新建标准</el-button>
        <span class="muted">共 {{ stTotal }} 条</span>
      </div>

      <el-table :data="standards" v-loading="stLoading" border size="small">
        <el-table-column prop="standardCode" label="标准编码" width="150" />
        <el-table-column prop="standardName" label="名称" min-width="160" />
        <el-table-column prop="securityType" label="保障类型" width="150">
          <template #default="{ row }">{{ enumLabel('securityType', row.securityType) }}</template>
        </el-table-column>
        <el-table-column prop="subsidyMode" label="补贴方式" width="130">
          <template #default="{ row }">
            {{ row.subsidyModeLabel || enumLabel('subsidyMode', row.subsidyMode) }}
          </template>
        </el-table-column>
        <el-table-column prop="subsidyValue" label="补贴值" width="110" />
        <el-table-column prop="maxAmount" label="封顶金额" width="110" />
        <el-table-column label="有效期" min-width="200">
          <template #default="{ row }">
            {{ row.effectiveStart || '—' }} ~ {{ row.effectiveEnd || '长期' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
              {{ row.status === 'ENABLED' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                       @click="toggleStandard(row)">
              {{ row.status === 'ENABLED' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="stTotal" :page-size="stQuery.pageSize"
                     :current-page="stQuery.pageNum"
                     @current-change="(p) => { stQuery.pageNum = p; loadStandards() }" />
    </div>

    <!-- 新建补贴标准 -->
    <el-dialog v-model="standardVisible" title="新建补贴标准" width="580px">
      <el-form :model="sf" label-width="120px">
        <el-form-item label="标准编码" required>
          <el-input v-model="sf.standardCode" placeholder="如 SUB-PUBLIC-2026" />
        </el-form-item>
        <el-form-item label="标准名称" required>
          <el-input v-model="sf.standardName" />
        </el-form-item>
        <el-form-item label="保障类型" required>
          <el-select v-model="sf.securityType" style="width:100%">
            <el-option label="公租房" value="PUBLIC" />
            <el-option label="保障性租赁住房" value="AFFORDABLE" />
            <el-option label="人才公寓" value="TALENT" />
            <el-option label="廉租房" value="LOW_RENT" />
          </el-select>
        </el-form-item>
        <el-form-item label="补贴方式" required>
          <el-select v-model="sf.subsidyMode" style="width:100%">
            <el-option label="定额（元/月）" value="FIXED" />
            <el-option label="按面积（元/㎡·月）" value="BY_AREA" />
            <el-option label="按人（元/人·月）" value="BY_PERSON" />
            <el-option label="按租金比例（0~1）" value="RATIO" />
          </el-select>
        </el-form-item>
        <el-form-item label="补贴值" required>
          <el-input v-model.number="sf.subsidyValue" />
        </el-form-item>
        <el-form-item label="封顶金额">
          <el-input v-model.number="sf.maxAmount" />
        </el-form-item>
        <el-form-item label="生效起">
          <el-date-picker v-model="sf.effectiveStart" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="生效止">
          <el-date-picker v-model="sf.effectiveEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="补贴值含义随方式变化：定额=元/月；按面积=元/㎡·月；按人=元/人·月；比例=0~1" />
      <template #footer>
        <el-button @click="standardVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateStandard">保存</el-button>
      </template>
    </el-dialog>
"""

if '补贴标准' not in s:
    s = s.replace("""    <el-dialog v-model="batchVisible" title="批量发放补贴" width="480px">""",
                  TPL + """
    <el-dialog v-model="batchVisible" title="批量发放补贴" width="480px">""", 1)

SCRIPT = """
// ---------------- 补贴标准 ----------------
const standards = ref([])
const stTotal = ref(0)
const stLoading = ref(false)
const standardVisible = ref(false)
const stQuery = reactive({ pageNum: 1, pageSize: 20, securityType: undefined,
  subsidyMode: undefined, keyword: '' })
const sf = reactive({ standardCode: '', standardName: '', securityType: 'PUBLIC',
  subsidyMode: 'FIXED', subsidyValue: null, maxAmount: null,
  effectiveStart: '', effectiveEnd: '' })

async function loadStandards() {
  stLoading.value = true
  try {
    const d = await req.get('/fin/subsidies/standards', {
      params: { pageNum: stQuery.pageNum, pageSize: stQuery.pageSize,
        securityType: stQuery.securityType || undefined,
        subsidyMode: stQuery.subsidyMode || undefined,
        keyword: stQuery.keyword || undefined }
    })
    standards.value = d.rows || []
    stTotal.value = Number(d.total || 0)
  } catch (e) {
    standards.value = []; stTotal.value = 0
  } finally { stLoading.value = false }
}

function openStandard() {
  Object.assign(sf, { standardCode: '', standardName: '', securityType: 'PUBLIC',
    subsidyMode: 'FIXED', subsidyValue: null, maxAmount: null,
    effectiveStart: '', effectiveEnd: '' })
  standardVisible.value = true
}

async function doCreateStandard() {
  if (!sf.standardCode || !sf.standardName || sf.subsidyValue === null) {
    ElMessage.warning('编码、名称、补贴值为必填'); return
  }
  saving.value = true
  try {
    await req.post('/fin/subsidies/standards', { ...sf })
    ElMessage.success('标准已创建')
    standardVisible.value = false
    loadStandards()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally { saving.value = false }
}

async function toggleStandard(row) {
  const enabled = row.status !== 'ENABLED'
  await ElMessageBox.confirm(
    `确认${enabled ? '启用' : '停用'}标准「${row.standardName}」？`, '提示',
    { type: 'warning' })
  await req.post(`/fin/subsidies/standards/${row.id}/status`, { enabled })
  ElMessage.success('已更新')
  loadStandards()
}
"""

if 'loadStandards' not in s:
    s = s.replace('</script>', SCRIPT + '</script>', 1)
    s = s.replace("onMounted(() => { load() })",
                  "onMounted(() => { load(); loadStandards() })", 1)

# 枚举补充
P2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                  'frontend', 'src', 'constants', 'enums.js')
e = io.open(P2, encoding='utf-8').read()
if 'subsidyMode:' not in e:
    e = e.replace("""  payStatus: {""",
                  """  subsidyMode: {
    FIXED: '定额', BY_AREA: '按面积', BY_PERSON: '按人', RATIO: '按租金比例'
  },
  payStatus: {""", 1)
    io.open(P2, 'w', encoding='utf-8', newline='').write(e)
    print('enums 已补 subsidyMode')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Subsidies.vue 已加补贴标准区块')
