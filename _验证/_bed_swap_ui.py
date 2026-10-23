# -*- coding: utf-8 -*-
"""床位视图增加「调换」操作：在租床位可一键换到同房间的空床位。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src',
                 'views', 'Houses.vue')
s = io.open(V, encoding='utf-8').read()

if 'doSwapBed' in s:
    print('已存在')
    raise SystemExit(0)

# 1) 表格加操作列
anchor = '<el-table-column prop="rentStandard" label="月租" width="100" />'
if anchor not in s:
    raise SystemExit('未找到床位表列')
s = s.replace(anchor, anchor + '''
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button v-if="row.occupied" link type="primary"
                       @click="openSwapBed(row)">调换</el-button>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>''', 1)

# 2) 调换弹窗
dialog = '''
    <!-- 床位调换 -->
    <el-dialog v-model="swapVisible" title="床位调换" width="480px">
      <el-alert type="info" :closable="false" show-icon
                title="调换后原床位立即释放，合同租金与期限保持不变" />
      <el-form :model="swapForm" label-width="90px" style="margin-top:12px">
        <el-form-item label="当前床位">
          <span>{{ swapForm.fromBed }}（{{ swapForm.occupant }}）</span>
        </el-form-item>
        <el-form-item label="目标床位" required>
          <el-select v-model="swapForm.targetHouseId" style="width:100%"
                     placeholder="选择同房间的空床位">
            <el-option v-for="b in freeBeds" :key="b.houseId"
                       :label="b.bedName + '（月租 ' + (b.rentStandard || 0) + '）'"
                       :value="b.houseId" />
          </el-select>
        </el-form-item>
        <el-form-item label="调换原因">
          <el-input v-model="swapForm.reason" placeholder="如：室友调整、设备维修" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="swapVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSwapBed">确认调换</el-button>
      </template>
    </el-dialog>
'''
i = s.rfind('</template>')
s = s[:i] + dialog + s[i:]

# 3) 逻辑
script = '''
/** 床位调换 */
const swapVisible = ref(false)
const swapForm = reactive({ contractId: '', fromBed: '', occupant: '',
  targetHouseId: '', reason: '' })
const freeBeds = computed(() =>
  bedRows.value.filter((b) => !b.occupied && b.houseId))

function openSwapBed(row) {
  if (!row.contractNo) {
    ElMessage.warning('该床位缺少合同信息，无法调换')
    return
  }
  Object.assign(swapForm, { contractId: '', fromBed: row.bedName,
    occupant: row.occupant || '', targetHouseId: '', reason: '' })
  // 用合同号反查合同 ID 由后端承担；此处通过合同列表接口拿 ID
  req.get('/contracts', { params: { pageNum: 1, pageSize: 50, keyword: row.contractNo } })
    .then((res) => {
      const list = (res && res.rows) || []
      const hit = list.find((c) => c.contractNo === row.contractNo)
      if (!hit) { ElMessage.warning('未找到对应合同'); return }
      swapForm.contractId = hit.id
      swapVisible.value = true
    })
    .catch(() => ElMessage.error('查询合同失败'))
}

async function doSwapBed() {
  if (!swapForm.targetHouseId) { ElMessage.warning('请选择目标床位'); return }
  saving.value = true
  try {
    await req.post(`/contracts/${swapForm.contractId}/swap-bed`, {
      targetHouseId: swapForm.targetHouseId, reason: swapForm.reason
    })
    ElMessage.success('床位已调换')
    swapVisible.value = false
    await loadBeds()
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '调换失败')
  } finally { saving.value = false }
}
'''
a = s.find('onMounted(')
s = s[:a] + script + '\n' + s[a:]

if "import { computed" not in s:
    s = s.replace("import { ref, reactive", "import { computed, ref, reactive", 1)

io.open(V, 'w', encoding='utf-8', newline='').write(s)
print('Houses.vue：床位调换已加')
