# -*- coding: utf-8 -*-
"""修复：
1) 组织/用户弹窗被误插进表格列插槽（每行渲染一个 → 多重遮罩叠加，页面变黑）
   → 移到根级，并给组织编辑补「标准地址」级联，详情补「标准地址」整行
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWS = os.path.join(HERE, '..', 'frontend', 'src', 'views')


def move_block(text, start_marker, end_marker, new_block):
    """把 start_marker..end_marker 之间的块替换为 new_block，并移动到根级末尾。"""
    i = text.find(start_marker)
    if i < 0:
        raise SystemExit('找不到起始标记: ' + start_marker)
    j = text.find(end_marker, i)
    if j < 0:
        raise SystemExit('找不到结束标记: ' + end_marker)
    j += len(end_marker)
    text = text[:i] + text[j:]
    k = text.rstrip().rfind('</template>')
    text = text[:k] + new_block + '\n' + text[k:]
    return text


# ============ 组织 ============
P = os.path.join(VIEWS, 'Orgs.vue')
s = io.open(P, encoding='utf-8').read()

if s.find('el-dialog v-model="detailVisible"') < s.find('</el-table-column>'):
    NEW_ORG = '''    <el-dialog v-model="detailVisible" title="组织详情" width="680px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="组织名称">{{ detailRow.orgName }}</el-descriptions-item>
        <el-descriptions-item label="编码">{{ detailRow.orgCode }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ enumLabel('orgType', detailRow.orgType) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ enumLabel('status', detailRow.status) }}</el-descriptions-item>
        <el-descriptions-item label="标准地址" :span="2">
          {{ standardAddress(detailRow) }}
        </el-descriptions-item>
        <el-descriptions-item label="社区/村">{{ detailRow.community || '—' }}</el-descriptions-item>
        <el-descriptions-item label="详细地址">{{ detailRow.address || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑组织" width="640px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="组织名称" required><el-input v-model="editForm.orgName" /></el-form-item>
        <el-form-item label="编码" required><el-input v-model="editForm.orgCode" /></el-form-item>
        <el-form-item label="标准地址">
          <el-cascader v-model="editRegionPath" :props="regionProps" clearable filterable
                       placeholder="省 / 地市 / 区县 / 街道乡镇（点击逐级选择）"
                       style="width:100%" @change="onEditRegionChange" />
        </el-form-item>
        <el-form-item label="社区/村"><el-input v-model="editForm.community" /></el-form-item>
        <el-form-item label="详细地址"><el-input v-model="editForm.address" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="editForm.sortNo" :min="1" /></el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
'''
    s = move_block(s, '    <el-dialog v-model="detailVisible"',
                   '    </el-dialog>\n', NEW_ORG)
    # 上面只截到第一个 </el-dialog>，需要再清理残留的编辑弹窗
    if 'el-dialog v-model="editVisible"' in s and s.find('el-dialog v-model="editVisible"') < s.find('</el-table-column>'):
        i = s.find('    <el-dialog v-model="editVisible"')
        j = s.find('    </el-dialog>', i) + len('    </el-dialog>\n')
        s = s[:i] + s[j:]

    # 补脚本：标准地址格式化 + 编辑级联
    if 'function standardAddress' not in s:
        ADD = '''
/** 标准地址：省市区街道拼接 */
function standardAddress(row) {
  const parts = [row.province, row.city, row.district, row.street].filter(Boolean)
  return parts.length ? parts.join(' / ') : '—'
}

/** 编辑弹窗内的标准地址级联 */
const editRegionPath = ref([])

function onEditRegionChange(codes) {
  if (!codes || !codes.length) {
    editForm.province = ''; editForm.city = ''
    editForm.district = ''; editForm.street = ''
    return
  }
  req.get('/sys/regions/path', { params: { code: codes[codes.length - 1] } })
    .then((path) => {
      const names = (path || []).map((x) => x.name)
      editForm.province = names[0] || ''
      editForm.city = names[1] || ''
      editForm.district = names[2] || ''
      editForm.street = names[3] || ''
    })
    .catch(() => {})
}
'''
        anchor = 'function openCreate'
        s = s.replace(anchor, ADD + '\n' + anchor, 1)

    # openEdit 里带上省市区街道
    s = s.replace('''    sortNo: row.sortNo || 1, remark: row.remark
  })''', '''    sortNo: row.sortNo || 1, remark: row.remark,
    province: row.province, city: row.city,
    district: row.district, street: row.street
  })
  editRegionPath.value = [row.province, row.city, row.district, row.street]
    .filter(Boolean)''')

    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('组织：弹窗已移到根级，编辑补标准地址')

# ============ 用户 ============
P = os.path.join(VIEWS, 'Rbac.vue')
s = io.open(P, encoding='utf-8').read()

if 'el-dialog v-model="userDetailVisible"' in s and \
        s.find('el-dialog v-model="userDetailVisible"') < s.find('</el-table-column>'):
    i = s.find('    <el-dialog v-model="userDetailVisible"')
    j = s.find('    </el-dialog>', s.find('    <el-dialog v-model="userEditVisible"'))
    j = s.find('    </el-dialog>', j + 1) + len('    </el-dialog>\n')
    block = s[i:j]
    s = s[:i] + s[j:]
    k = s.rstrip().rfind('</template>')
    s = s[:k] + block + '\n' + s[k:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('用户：弹窗已移到根级（修复多重遮罩变黑）')
