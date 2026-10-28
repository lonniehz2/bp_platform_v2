# -*- coding: utf-8 -*-
"""Houses：组织列 + 入住信息。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'Houses.vue')
s = io.open(p, encoding='utf-8').read()

if 'label="组织"' not in s:
    s = s.replace('''      <el-table-column label="所属空间" width="170" show-overflow-tooltip>''',
                  '''      <el-table-column prop="orgId" label="组织" width="150">
        <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>
      </el-table-column>
      <el-table-column label="所属空间" width="170" show-overflow-tooltip>''', 1)
    s = s.replace('''          <el-button link @click="detail = row; show = true">详情</el-button>''',
                  '''          <el-button link @click="detail = row; show = true">详情</el-button>
          <el-button link type="primary" @click="openOccupancy(row)">入住信息</el-button>''', 1)
    s = s.replace('''    <el-dialog v-model="createVisible" title="新增房源" width="640px">''',
                  '''    <el-dialog v-model="occVisible" title="入住信息" width="560px">
      <el-descriptions v-if="occ && occ.occupied" :column="1" border size="small">
        <el-descriptions-item label="合同号">{{ occ.contractNo }}</el-descriptions-item>
        <el-descriptions-item label="租期">{{ occ.leaseStart }} ~ {{ occ.leaseEnd }}</el-descriptions-item>
        <el-descriptions-item label="承租人">{{ occ.tenantName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ occ.tenantPhone || '—' }}</el-descriptions-item>
        <el-descriptions-item label="已入住人数">{{ occ.tenantCount }} 人</el-descriptions-item>
        <el-descriptions-item label="同住人">
          <div v-if="!occ.cohabitants || !occ.cohabitants.length" class="muted">无</div>
          <div v-for="(c, i) in occ.cohabitants" :key="i">
            {{ c.name }}（{{ c.relation || '同住' }}）{{ c.id_card_mask || '' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
      <el-empty v-else description="该房源当前无有效合同" />
      <template #footer>
        <el-button @click="occVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="createVisible" title="新增房源" width="640px">''', 1)
    if 'const occVisible' not in s:
        s = s.replace('''const show = ref(false)''', '''const occVisible = ref(false)
const occ = ref(null)

async function openOccupancy(row) {
  occ.value = null
  occVisible.value = true
  try {
    occ.value = await req.get('/houses/' + row.id + '/occupancy')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '查询入住信息失败')
  }
}

const show = ref(false)''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('Houses 组织列/入住信息已加')
else:
    print('Houses 已存在')
