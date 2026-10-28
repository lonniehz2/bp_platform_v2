<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">公示管理</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:170px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>

    </div>
    <el-alert v-if="'配租公示必须 ≥7 自然日且已结束才能签约'" type="info" :closable="false" show-icon :title="'配租公示必须 ≥7 自然日且已结束才能签约'"
              style="margin-bottom:12px" />
    <el-table empty-text="暂无公示，配租/资格公示从这里发起" :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
      <template #default="{ row }">
        <div style="padding:8px 12px">
          <div style="margin-bottom:6px">
            <strong>中签名单</strong>
            <span class="muted" style="margin-left:8px;font-size:12px">
              {{ winnersOf(row.id).length ? `共 ${winnersOf(row.id).length} 人` : '暂无中签记录（需先关联批次并完成摇号）' }}
            </span>
          </div>
          <el-table v-if="winnersOf(row.id).length" :data="winnersOf(row.id)"
                    size="small" border max-height="320">
            <el-table-column prop="lotterySeq" label="摇号序号" width="100" />
            <el-table-column prop="personName" label="姓名" width="110" />
            <el-table-column prop="idCardMask" label="身份证（脱敏）" width="190" />
            <el-table-column prop="phoneMask" label="手机（脱敏）" width="140" />
            <el-table-column prop="houseName" label="中签房源" min-width="170" />
            <el-table-column prop="selectSeq" label="选房序号" width="100" />
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row: w }">
                <el-button link type="primary" @click="goSignFromWinner(w)"
                           data-testid="winner-sign">去签约</el-button>
              </template>
            </el-table-column>
            <el-table-column prop="resultTypeLabel" label="结果" width="90">
              <template #default="{ row: w }">
                <el-tag size="small" :type="w.resultType === 'WON' ? 'success' : 'info'">
                  {{ w.resultTypeLabel }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </el-table-column>
      <el-table-column prop="publicityNo" label="公示号" width="170" />
      <el-table-column prop="publicityType" label="类型" width="130">
        <template #default="{ row }">{{ row.publicityTypeLabel || enumLabel('publicityType', row.publicityType) }}</template>
      </el-table-column>
      <el-table-column prop="title" label="标题" width="200" />
      <el-table-column prop="startDate" label="开始" width="110" />
      <el-table-column prop="endDate" label="结束" width="110" />
      <el-table-column prop="publicityStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.publicityStatusLabel || enumLabel('publicityStatus', row.publicityStatus) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="row.publicityStatus === 'PUBLISHED'"
                     @click="doPublish(row)">发布</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />
    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { publicityApi } from '@/api/modules'
import req from '@/api/request'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)


async function load() {
  loading.value = true
  try {
    const data = await publicityApi.page({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = data.rows || data || []
    total.value = Number(data.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }
function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}


/** 中签名单：按公示 ID 缓存 */
const winnersMap = reactive({})
function winnersOf(publicityId) {
  if (!publicityId) return []
  if (!(publicityId in winnersMap)) {
    winnersMap[publicityId] = []
    req.get(`/publicities/${publicityId}/winners`).then((list) => {
      winnersMap[publicityId] = list || []
    }).catch(() => { winnersMap[publicityId] = [] })
  }
  return winnersMap[publicityId]
}

/** 可关联的配租批次 */
const batchOptions = ref([])
async function loadBatches() {
  if (batchOptions.value.length) return
  try {
    const d = await req.get('/allocation/batches', { params: { pageNum: 1, pageSize: 100 } })
    batchOptions.value = (d && d.rows) || []
  } catch (e) { batchOptions.value = [] }
}


/** 从名单一键签约：带人中转合同页的快捷签约 */
function goSignFromWinner(w) {
  if (!w.personId) { ElMessage.warning('该记录缺少中签人信息'); return }
  router.push({ path: '/contracts',
    query: { personId: String(w.personId), houseId: w.houseId ? String(w.houseId) : '' } })
}

const router = useRouter()

onMounted(load)
/** 发布公示（发布后对外可见，进入公示期） */
async function doPublish(row) {
  await ElMessageBox.confirm(
    `确认发布「${row.publicityTitle || row.publicityNo}」？发布后进入公示期。`,
    '发布公示', { type: 'warning' })
  await req.post(`/publicities/${row.id}/publish`)
  ElMessage.success('已发布'); load()
}
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
