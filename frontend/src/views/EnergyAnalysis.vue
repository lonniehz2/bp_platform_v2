<template>
  <div>
    <div class="toolbar">
      <el-radio-group v-model="months" size="small" @change="load">
        <el-radio-button :value="3">{{ t('energyAnalysis.last3') }}</el-radio-button>
        <el-radio-button :value="6">{{ t('energyAnalysis.last6') }}</el-radio-button>
        <el-radio-button :value="12">{{ t('energyAnalysis.last12') }}</el-radio-button>
      </el-radio-group>
      <span class="muted" style="font-size:12px">
        {{ t('energyAnalysis.formula') }}
      </span>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="8">
        <el-card shadow="never"><div class="muted">{{ t('energyAnalysis.windowUsage') }}</div>
          <div style="font-size:22px;font-weight:600">{{ totalUsage }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never"><div class="muted">{{ t('energyAnalysis.totalAmount') }}</div>
          <div style="font-size:22px;font-weight:600">{{ totalAmount }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never"><div class="muted">{{ t('energyAnalysis.readingCount') }}</div>
          <div style="font-size:22px;font-weight:600">{{ totalReadings }}</div>
        </el-card>
      </el-col>
    </el-row>

    <div style="font-weight:600;margin-bottom:6px">{{ t('energyAnalysis.byItem') }}</div>
    <el-table :data="itemRows" size="small" border style="margin-bottom:14px">
      <el-table-column prop="feeItemName" :label="t('energyAnalysis.item')" width="190" />
      <el-table-column prop="readings" :label="t('energyAnalysis.readings')" width="110" />
      <el-table-column prop="usage" :label="t('energyAnalysis.usage')" width="150" />
      <el-table-column :label="t('energyAnalysis.amount')" width="150" >
          <template #default="{ row }">{{ $money(row.amount) }}</template>
        </el-table-column>
    </el-table>

    <el-row :gutter="12" style="margin-bottom:6px">
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:2px">{{ t('energyAnalysis.usageTrend') }}</div>
        <LineTrend :rows="usageTrend" :unit="t('energyAnalysis.unitUsage')" color="#409eff" :height="200" />
      </el-col>
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:2px">{{ t('energyAnalysis.amountTrend') }}</div>
        <LineTrend :rows="amountTrend" :unit="t('energyAnalysis.unitCny')" color="#e6a23c" :height="200" />
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:6px">{{ t('energyAnalysis.monthly') }}</div>
        <el-table :data="monthRows" size="small" border max-height="300">
          <el-table-column prop="month" :label="t('energyAnalysis.month')" width="110" />
          <el-table-column prop="readings" :label="t('energyAnalysis.readings')" width="100" />
          <el-table-column prop="usage" :label="t('energyAnalysis.usage')" />
          <el-table-column :label="t('energyAnalysis.amount')" >
          <template #default="{ row }">{{ $money(row.amount) }}</template>
        </el-table-column>
        </el-table>
      </el-col>
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:6px">{{ t('energyAnalysis.buildingSummary') }}</div>
        <el-table :data="buildings" size="small" border max-height="300">
          <el-table-column prop="building" :label="t('energyAnalysis.building')" />
          <el-table-column prop="usage" :label="t('energyAnalysis.usage')" width="140" />
        </el-table>
      </el-col>
    </el-row>

    <div style="font-weight:600;margin:14px 0 6px">{{ t('energyAnalysis.topHouses') }}</div>
    <el-table :data="top" size="small" border max-height="360">
      <el-table-column prop="houseCode" :label="t('energyAnalysis.houseCode')" width="170" />
      <el-table-column prop="houseName" :label="t('energyAnalysis.houseName')" min-width="200" />
      <el-table-column prop="building" :label="t('energyAnalysis.building')" width="120" />
      <el-table-column prop="usage" :label="t('energyAnalysis.usage')" width="110" />
    </el-table>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * 能耗分析：按月份、楼栋与房源统计水电等计量用量。
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import LineTrend from '@/components/LineTrend.vue'

const { t } = useI18n()
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
    ElMessage.error(e?.response?.data?.message || t('energyAnalysis.loadFailed'))
  }
}

onMounted(load)
</script>
