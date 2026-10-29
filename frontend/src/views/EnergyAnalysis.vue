<template>
  <div>
    <div class="toolbar">
      <el-radio-group v-model="months" size="small" @change="load">
        <el-radio-button :value="3">近 3 月</el-radio-button>
        <el-radio-button :value="6">近 6 月</el-radio-button>
        <el-radio-button :value="12">近 12 月</el-radio-button>
      </el-radio-group>
      <span class="muted" style="font-size:12px">
        用量 = 本次读数 − 上次读数（跨月衔接）；金额 = 用量 × 计费项目单价
      </span>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="8">
        <el-card shadow="never"><div class="muted">本窗口用量合计</div>
          <div style="font-size:22px;font-weight:600">{{ totalUsage }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never"><div class="muted">金额合计</div>
          <div style="font-size:22px;font-weight:600">{{ totalAmount }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never"><div class="muted">读数次数</div>
          <div style="font-size:22px;font-weight:600">{{ totalReadings }}</div>
        </el-card>
      </el-col>
    </el-row>

    <div style="font-weight:600;margin-bottom:6px">按计量项目（水 / 电 / 燃气）</div>
    <el-table :data="itemRows" size="small" border style="margin-bottom:14px">
      <el-table-column prop="feeItemName" label="计量项目" width="190" />
      <el-table-column prop="readings" label="读数次数" width="110" />
      <el-table-column prop="usage" label="用量" width="150" />
      <el-table-column label="金额" width="150" >
          <template #default="{ row }">{{ $money(row.amount) }}</template>
        </el-table-column>
    </el-table>

    <el-row :gutter="12" style="margin-bottom:6px">
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:2px">用量趋势</div>
        <LineTrend :rows="usageTrend" unit="用量" color="#409eff" :height="200" />
      </el-col>
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:2px">金额趋势</div>
        <LineTrend :rows="amountTrend" unit="元" color="#e6a23c" :height="200" />
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:6px">月度明细</div>
        <el-table :data="monthRows" size="small" border max-height="300">
          <el-table-column prop="month" label="月份" width="110" />
          <el-table-column prop="readings" label="读数次数" width="100" />
          <el-table-column prop="usage" label="用量" />
          <el-table-column label="金额" >
          <template #default="{ row }">{{ $money(row.amount) }}</template>
        </el-table-column>
        </el-table>
      </el-col>
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:6px">楼栋汇总</div>
        <el-table :data="buildings" size="small" border max-height="300">
          <el-table-column prop="building" label="楼栋" />
          <el-table-column prop="usage" label="用量" width="140" />
        </el-table>
      </el-col>
    </el-row>

    <div style="font-weight:600;margin:14px 0 6px">用量 TOP 10 房源</div>
    <el-table :data="top" size="small" border max-height="360">
      <el-table-column prop="houseCode" label="房源编号" width="170" />
      <el-table-column prop="houseName" label="房源名称" min-width="200" />
      <el-table-column prop="building" label="楼栋" width="120" />
      <el-table-column prop="usage" label="用量" width="110" />
    </el-table>
  </div>
</template>

<script setup>
/**
 * 能耗分析：按月份、楼栋与房源统计水电等计量用量。
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import LineTrend from '@/components/LineTrend.vue'

const months = ref(6)
const monthRows = ref([])
const buildings = ref([])
const top = ref([])
const itemRows = ref([])

/** 折线图数据：用量 / 金额（月份显示为 MM） */
const usageTrend = computed(() => monthRows.value.map((m) => ({
  label: String(m.month || '').slice(5), value: Number(m.usage) || 0
})))
const amountTrend = computed(() => monthRows.value.map((m) => ({
  label: String(m.month || '').slice(5), value: Number(m.amount) || 0
})))

const totalUsage = computed(() =>
  monthRows.value.reduce((s, m) => s + Number(m.usage || 0), 0).toFixed(2))
const totalAmount = computed(() =>
  monthRows.value.reduce((s, m) => s + Number(m.amount || 0), 0).toFixed(2))
const totalReadings = computed(() =>
  monthRows.value.reduce((s, m) => s + Number(m.readings || 0), 0))

async function load() {
  try {
    const r = await req.get('/fin/meter-readings/analytics', { params: { months: months.value } })
    const ms = (r && r.months) || []
    monthRows.value = ms.map((m) => ({
      month: m.month, readings: m.readings, usage: m.usage, amount: m.amount
    }))
    buildings.value = (r && r.byBuilding) || []
    top.value = (r && r.topHouses) || []
    itemRows.value = (r && r.byFeeItem) || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载能耗数据失败')
  }
}

onMounted(load)
</script>
