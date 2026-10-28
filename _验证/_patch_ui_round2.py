# -*- coding: utf-8 -*-
"""前端：公示组织/签约状态、配租单状态、房源组织与入住信息。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')

# ---------- Publicities ----------
p = os.path.join(V, 'Publicities.vue')
s = io.open(p, encoding='utf-8').read()
if "label=\"组织\"" not in s:
    s = s.replace('''            <el-table-column prop="houseName" label="中签房源" min-width="170" />''',
                  '''            <el-table-column prop="orgName" label="组织" width="150" />
            <el-table-column prop="houseName" label="中签房源" min-width="170" />''', 1)
    s = s.replace('''      <el-table-column prop="publicityNo" label="公示号" width="170" />''',
                  '''      <el-table-column prop="publicityNo" label="公示号" width="170" />
      <el-table-column prop="orgId" label="组织" width="150">
        <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>
      </el-table-column>''', 1)
    # 签约按钮状态
    s = s.replace('''              <template #default="{ row: w }">
                <el-button link type="primary" @click="goSignFromWinner(w)"
                           data-testid="winner-sign">去签约</el-button>
              </template>''', '''              <template #default="{ row: w }">
                <el-tag v-if="w.allocationStatus === 'SIGNED'" size="small" type="success">
                  已签约
                </el-tag>
                <el-button v-else link type="primary" @click="goSignFromWinner(w)"
                           data-testid="winner-sign">去签约</el-button>
              </template>''', 1)
    s = s.replace('''function goSignFromWinner(w) {
  if (!w.personId) { ElMessage.warning('该记录缺少中签人信息'); return }''', '''function goSignFromWinner(w) {
  if (!w.personId) { ElMessage.warning('该记录缺少中签人信息'); return }
  if (w.allocationStatus === 'SIGNED') { ElMessage.info('该中签人已签约'); return }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('公示页已加组织列/签约状态')

# ---------- Allocations ----------
p = os.path.join(V, 'Allocations.vue')
s = io.open(p, encoding='utf-8').read()
if '已签约' not in s:
    s = s.replace('''          <template #default="{ row }">
            <el-button link type="success" :disabled="!!row.lockOverdue"
                       @click="sign(row)">签约</el-button>
          </template>''', '''          <template #default="{ row }">
            <el-tag v-if="row.allocationStatus === 'SIGNED'" size="small" type="success">已签约</el-tag>
            <el-button v-else link type="success" :disabled="!!row.lockOverdue"
                       @click="sign(row)">去签约</el-button>
          </template>''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('配租单签约状态已改')

# ---------- Houses：组织列 + 入住信息 ----------
p = os.path.join(V, 'Houses.vue')
s = io.open(p, encoding='utf-8').read()
if '入住信息' not in s:
    s = s.replace('''      <el-table-column prop="spaceId" label="所属空间"''',
                  '''      <el-table-column prop="orgId" label="组织" width="150">
        <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>
      </el-table-column>
      <el-table-column prop="spaceId" label="所属空间"''', 1)
    s = s.replace('''            <el-button link type="primary" @click="openDetail(row)">详情</el-button>''',
                  '''            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button link type="primary" @click="openOccupancy(row)">入住信息</el-button>''', 1)
    # 弹窗
    s = s.replace('''    <!-- 批量导入 -->''', '''    <!-- 入住信息 -->
    <el-dialog v-model="occVisible" title="入住信息" width="560px">
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

    <!-- 批量导入 -->''', 1)
    if 'const occVisible' not in s:
        s = s.replace('''const impVisible = ref(false)''', '''const occVisible = ref(false)
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

const impVisible = ref(false)''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('房源页已加组织列/入住信息')
