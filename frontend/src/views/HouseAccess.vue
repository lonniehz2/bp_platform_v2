<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 style="margin:0">{{ t('houseAccess.pageTitle') }}</h2>
      <span class="muted">{{ t('houseAccess.pageHint') }}</span>
    </div>

    <el-form inline style="margin-top:12px" @submit.prevent>
      <el-form-item :label="t('houseAccess.house')">
        <el-input v-model="keyword" clearable :placeholder="t('houseAccess.searchHint')"
                  style="width:280px" @keyup.enter="load" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="load">{{ t('common.search') }}</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="houseCode" :label="t('house.code')" width="170" />
      <el-table-column prop="houseName" :label="t('house.name')" min-width="160" />
      <el-table-column :label="t('house.statusCol')" width="110">
        <template #default="{ row }">{{ enumLabel('houseStatus', row.houseStatus) || row.houseStatus }}</template>
      </el-table-column>
      <el-table-column :label="t('house.actions')" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="open(row)">{{ t('houseAccess.openPanel') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <HouseAccessPanel v-model="visible" :house-id="selected?.id" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'
import HouseAccessPanel from '@/components/HouseAccessPanel.vue'

const { t } = useI18n()
const keyword = ref('')
const rows = ref([])
const loading = ref(false)
const visible = ref(false)
const selected = ref(null)

async function load() {
  loading.value = true
  try {
    const d = await req.get('/houses', { params: { pageNum: 1, pageSize: 30, keyword: keyword.value || undefined } })
    rows.value = d.rows || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('houseAccess.loadFailed'))
  } finally { loading.value = false }
}

function open(row) {
  selected.value = row
  visible.value = true
}

onMounted(load)
</script>
