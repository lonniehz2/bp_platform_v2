# -*- coding: utf-8 -*-
"""补：设备数据新鲜度提示 + 合同换床。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---------------- 设备新鲜度 ----------------
p = os.path.join(VIEWS, 'Devices.vue')
s = io.open(p, encoding='utf-8').read()
if 'freshness' not in s:
    s = s.replace('''    <el-table empty-text="暂无设备，可点「同步设备」从 IoT 拉取" :data="rows" v-loading="loading" border size="small">''',
                  '''    <el-alert v-if="fresh && fresh.stale > 0" type="warning" :closable="false" show-icon
              style="margin-bottom:10px"
              :title="'数据新鲜度：24 小时内上报 ' + fresh.fresh + ' / ' + fresh.total
                + ' 台（静默 ' + fresh.stale + ' 台，占 ' + fresh.staleRate + '%）'">
      <template #default>
        <el-button link type="primary" @click="freshVisible = true">查看静默设备</el-button>
      </template>
    </el-alert>

    <el-table empty-text="暂无设备，可点「同步设备」从 IoT 拉取" :data="rows" v-loading="loading" border size="small">''', 1)

    # 静默设备弹窗（放在导入弹窗前）
    s = s.replace('''    <!-- 设备批量导入 -->''', '''    <!-- 静默设备 -->
    <el-dialog v-model="freshVisible" title="24 小时未上报的设备" width="760px">
      <el-alert type="info" :closable="false" show-icon
                title="按静默时长倒序；长时间静默可能是离线、网关故障或未接入。" />
      <el-table :data="(fresh && fresh.staleDevices) || []" size="small" border
                max-height="380" style="margin-top:10px">
        <el-table-column prop="deviceId" label="设备编号" width="170" />
        <el-table-column prop="deviceName" label="名称" min-width="140" />
        <el-table-column prop="deviceType" label="类型" width="110" />
        <el-table-column prop="hoursSilent" label="静默(小时)" width="110" />
        <el-table-column prop="lastReportTime" label="最后上报" width="170" />
        <el-table-column prop="battery" label="电量" width="80" />
      </el-table>
    </el-dialog>

    <!-- 设备批量导入 -->''', 1)

    if 'const freshVisible' not in s:
        s = s.replace('''const impVisible = ref(false)''', '''const fresh = ref(null)
const freshVisible = ref(false)

async function loadFreshness() {
  try {
    fresh.value = await req.get('/devices/freshness', { params: { hours: 24 } })
  } catch (e) { fresh.value = null }
}

const impVisible = ref(false)''', 1)
        s = s.replace("onMounted(() => { loadTypes(); load() })",
                      "onMounted(() => { loadTypes(); load(); loadFreshness() })", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('设备新鲜度已加')

# ---------------- 合同换床 ----------------
p = os.path.join(VIEWS, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
if 'swapBed' not in s:
    # 行操作加按钮（放在详情后）
    s = s.replace('''            <el-button link type="primary" @click="openContractDetail(row)"
                       data-testid="contract-detail">详情</el-button>''',
                  '''            <el-button link type="primary" @click="openContractDetail(row)"
                       data-testid="contract-detail">详情</el-button>
            <el-button v-if="['EFFECTIVE','RENEWING'].includes(row.contractStatus)"
                       link type="warning" @click="openSwap(row)">换床</el-button>''', 1)

    # 弹窗
    s = s.replace('''    <!-- 快捷签约 -->''', '''    <!-- 换床 -->
    <el-dialog v-model="swapVisible" title="合同换床" width="560px">
      <el-alert type="info" :closable="false" show-icon
                title="换床会把合同迁到新房源所在空间，并同步占用流水；原房源释放。" />
      <el-form :model="sw" label-width="100px" style="margin-top:12px">
        <el-form-item label="合同">
          <el-input :model-value="sw.contractNo" disabled />
        </el-form-item>
        <el-form-item label="目标房源" required>
          <HouseSelect v-model="sw.targetHouseId" width="100%" testid="swap-house" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="sw.reason" type="textarea" :rows="2"
                    placeholder="如 原床位调整 / 房屋维修" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="swapVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSwap">确认换床</el-button>
      </template>
    </el-dialog>

    <!-- 快捷签约 -->''', 1)

    if 'const swapVisible' not in s:
        s = s.replace('''const qf = reactive({''', '''const swapVisible = ref(false)
const sw = reactive({ contractId: null, contractNo: '', targetHouseId: '', reason: '' })

function openSwap(row) {
  sw.contractId = row.id
  sw.contractNo = row.contractNo
  sw.targetHouseId = ''
  sw.reason = ''
  swapVisible.value = true
}

async function doSwap() {
  if (!sw.targetHouseId) { ElMessage.warning('请选择目标房源'); return }
  saving.value = true
  try {
    await req.post('/contracts/' + sw.contractId + '/swap-bed',
      { targetHouseId: sw.targetHouseId, reason: sw.reason || undefined })
    ElMessage.success('已换床')
    swapVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '换床失败')
  } finally { saving.value = false }
}

const qf = reactive({''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('合同换床已加')
