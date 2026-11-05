<template>
  <div class="house-card" :class="[statusClass, { frozen: row.frozen }]">
    <div class="card-head">
      <div class="room-name">{{ row.houseName || row.houseCode }}</div>
      <el-tag size="small" :type="tagType">{{ displayStatus }}</el-tag>
    </div>
    <div class="card-path">{{ row.spaceFullName || '-' }}</div>

    <div class="card-row">
      <span>{{ t('houseGrid.occupied') }}</span>
      <el-link type="primary" :underline="false" @click="$emit('occupancy', row)">
        {{ row.occupiedCount || 0 }}
      </el-link>
      <span>/ {{ row.capacity || '-' }}</span>
    </div>
    <div v-if="row.lesseeName" class="card-row">
      <span>{{ t('houseGrid.lessee') }}</span>
      <b>{{ row.lesseeName }}</b>
    </div>

    <div v-if="row.frozen" class="card-freeze">
      {{ t('houseGrid.frozen') }}：{{ row.freezeReason || '-' }}
    </div>

    <div v-if="row.lock" class="card-device">
      <div class="device-name">{{ row.lock.deviceName || t('houseGrid.lock') }}</div>
      <div class="device-line">{{ t('houseGrid.mac') }}：{{ row.lock.deviceMac || '-' }}</div>
      <div class="device-line">
        <span>{{ onlineText }}</span>
        <span>{{ t('houseGrid.battery') }}：{{ row.lock.battery != null ? row.lock.battery + '%' : '-' }}</span>
      </div>
    </div>
    <div v-else class="card-no-device">{{ t('houseGrid.noLock') }}</div>

    <div v-if="row.alertCount" class="card-alert">
      {{ t('houseGrid.alerts', { n: row.alertCount }) }}
    </div>

    <div class="card-actions">
      <el-button link size="small" @click="$emit('records', row)">{{ t('houseGrid.records') }}</el-button>
      <el-button link size="small" @click="$emit('access', row)">{{ t('houseGrid.personAuth') }}</el-button>
      <el-button link size="small" :type="row.frozen ? 'success' : 'danger'"
                 @click="$emit('freeze', row)">{{ row.frozen ? t('houseGrid.restore') : t('houseGrid.freeze') }}</el-button>
      <el-button link size="small" :disabled="!row.lock || row.lock.onlineStatus !== 1"
                 @click="$emit('open', row)">{{ t('houseGrid.remoteOpen') }}</el-button>
      <el-button link size="small" @click="$emit('access', row)">{{ t('houseGrid.emergency') }}</el-button>
      <el-button link size="small" @click="$emit('detail', row)">{{ t('houseGrid.detail') }}</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({ row: { type: Object, required: true } })
defineEmits(['records', 'access', 'freeze', 'open', 'detail', 'occupancy'])
const { t } = useI18n()

const displayStatus = computed(() => {
  if (props.row.frozen) return t('houseGrid.frozen')
  return props.row.houseStatusLabel || props.row.houseStatus || '-'
})
const tagType = computed(() => {
  if (props.row.frozen) return 'danger'
  if (props.row.alertCount) return 'warning'
  const s = props.row.houseStatus
  if (s === 'OCCUPIED') return 'success'
  if (s === 'VACANT') return 'warning'
  if (s === 'PENDING_ALLOC') return 'info'
  return 'info'
})
const statusClass = computed(() => {
  if (props.row.frozen) return 'frozen'
  const s = props.row.houseStatus
  return {
    OCCUPIED: 'occupied', VACANT: 'vacant', PENDING_ALLOC: 'pending',
    LOCKED: 'allocated', ALLOCATED: 'allocated', MAINTENANCE: 'maintenance',
    DISABLED: 'disabled'
  }[s] || ''
})
const onlineText = computed(() => {
  if (props.row.lock?.installStatus === 'PENDING_INSTALL') return t('houseGrid.pendingInstall')
  return props.row.lock?.onlineStatus === 1 ? t('houseGrid.online') : t('houseGrid.offline')
})
</script>

<style scoped>
.house-card { border: 1px solid var(--el-border-color); border-left: 5px solid var(--el-border-color); border-radius: 6px; padding: 8px 10px; min-height: 200px; background: var(--el-bg-color); display: flex; flex-direction: column; gap: 5px; }
.house-card.occupied { border-left-color: #67c23a; }
.house-card.vacant { border-left-color: #e6a23c; }
.house-card.pending { border-left-color: #8b5cf6; }
.house-card.allocated { border-left-color: #409eff; }
.house-card.maintenance { border-left-color: #ff7a45; }
.house-card.disabled { border-left-color: #909399; }
.house-card.frozen { border-left-color: #f56c6c; background: rgba(245,108,108,.05); }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.room-name { font-weight: 600; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-path { color: var(--el-text-color-secondary); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-row { display: flex; gap: 8px; font-size: 13px; }
.card-row span { color: var(--el-text-color-secondary); }
.card-freeze { color: #f56c6c; font-size: 12px; }
.card-device { border-top: 1px dashed var(--el-border-color-lighter); padding-top: 5px; font-size: 12px; }
.device-name { font-weight: 500; }
.device-line { color: var(--el-text-color-secondary); display: flex; justify-content: space-between; }
.card-no-device { color: #e6a23c; font-size: 12px; }
.card-alert { color: #f56c6c; font-size: 12px; }
.card-actions { margin-top: auto; border-top: 1px solid var(--el-border-color-lighter); padding-top: 6px; display: flex; flex-wrap: wrap; gap: 2px 4px; }
.card-actions :deep(.el-button) { margin-left: 0; padding: 0 2px; font-size: 12px; }
</style>
