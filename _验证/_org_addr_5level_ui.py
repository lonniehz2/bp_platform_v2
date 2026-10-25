# -*- coding: utf-8 -*-
"""组织页：标准地址改为五级（省/市/区县/街道 + 社区可下拉可手填），并保存各级代码。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'Orgs.vue')
s = io.open(V, encoding='utf-8').read()

# ---------- 1) 新增弹窗：社区改为可下拉可输入 ----------
OLD_COMMUNITY_CREATE = '''        <el-form-item label="社区/村">
          <el-input v-model="f.community" placeholder="社区、村委会名称（可手填）" /></el-form-item>'''
NEW_COMMUNITY_CREATE = '''        <el-form-item label="社区/村">
          <el-select v-model="f.community" filterable allow-create default-first-option
                     clearable placeholder="可从下拉选择，也可直接输入新社区名"
                     style="width:100%">
            <el-option v-for="c in communityOptions" :key="c" :label="c" :value="c" />
          </el-select>
          <div class="muted" style="font-size:12px;margin-top:4px">
            第五级（社区/村）允许手填：区划库未收录时直接输入即可
          </div>
        </el-form-item>'''
if OLD_COMMUNITY_CREATE in s:
    s = s.replace(OLD_COMMUNITY_CREATE, NEW_COMMUNITY_CREATE, 1)
    print('新增弹窗：社区改为可下拉可手填')

# ---------- 2) 编辑弹窗：补标准地址级联 + 社区下拉 ----------
OLD_EDIT = '''        <el-form-item label="社区/村"><el-input v-model="editForm.community" /></el-form-item>'''
NEW_EDIT = '''        <el-form-item label="社区/村">
          <el-select v-model="editForm.community" filterable allow-create
                     default-first-option clearable
                     placeholder="可从下拉选择，也可直接输入" style="width:100%">
            <el-option v-for="c in communityOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>'''
if OLD_EDIT in s:
    s = s.replace(OLD_EDIT, NEW_EDIT, 1)
    print('编辑弹窗：社区改为可下拉可手填')
else:
    print('编辑弹窗社区未匹配')

# ---------- 3) 级联选择后写入各级名称与代码 ----------
OLD_CHANGE = '''function onRegionChange(codes) {
  if (!codes || !codes.length) {
    f.province = ''; f.city = ''; f.district = ''; f.street = ''
    return
  }'''
NEW_CHANGE = '''function onRegionChange(codes) {
  if (!codes || !codes.length) {
    f.province = ''; f.city = ''; f.district = ''; f.street = ''
    f.provinceCode = ''; f.cityCode = ''; f.districtCode = ''; f.streetCode = ''
    communityOptions.value = []
    return
  }
  // 代码逐级落到表单，供后端保存（第五级社区允许手填，故不存代码）
  f.provinceCode = codes[0] || ''
  f.cityCode = codes[1] || ''
  f.districtCode = codes[2] || ''
  f.streetCode = codes[3] || ''
  if (f.streetCode) {
    loadCommunities(f.streetCode)
  }'''
if OLD_CHANGE in s:
    s = s.replace(OLD_CHANGE, NEW_CHANGE, 1)
    print('新增：级联已写代码')
else:
    print('onRegionChange 未匹配')

# ---------- 4) 编辑弹窗级联：同样写代码 ----------
OLD_ECHANGE = '''function onEditRegionChange(codes) {
  if (!codes || !codes.length) {
    editForm.province = ''; editForm.city = ''
    editForm.district = ''; editForm.street = ''
    return
  }'''
NEW_ECHANGE = '''function onEditRegionChange(codes) {
  if (!codes || !codes.length) {
    editForm.province = ''; editForm.city = ''
    editForm.district = ''; editForm.street = ''
    editForm.provinceCode = ''; editForm.cityCode = ''
    editForm.districtCode = ''; editForm.streetCode = ''
    return
  }
  editForm.provinceCode = codes[0] || ''
  editForm.cityCode = codes[1] || ''
  editForm.districtCode = codes[2] || ''
  editForm.streetCode = codes[3] || ''
  if (editForm.streetCode) {
    loadCommunities(editForm.streetCode)
  }'''
if OLD_ECHANGE in s:
    s = s.replace(OLD_ECHANGE, NEW_ECHANGE, 1)
    print('编辑：级联已写代码')
else:
    print('onEditRegionChange 未匹配')

# ---------- 5) 社区下拉选项加载 ----------
if 'loadCommunities' not in s.split('function onRegionChange')[0]:
    ADD = '''
/** 社区选项：优先取区划库第五级，其次取已有组织里用过的社区名 */
const communityOptions = ref([])

async function loadCommunities(streetCode) {
  const set = new Set()
  try {
    const list = await req.get('/sys/regions/children', { params: { parentCode: streetCode } })
    ;(list || []).forEach((r) => r.name && set.add(r.name))
  } catch (e) { /* 区划库未收录第五级时忽略 */ }
  // 合并历史输入，便于复用
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    ;(d.rows || d || []).forEach((o) => o.community && set.add(o.community))
  } catch (e) { /* 忽略 */ }
  communityOptions.value = Array.from(set)
}
'''
    anchor = 'function onRegionChange'
    s = s.replace(anchor, ADD + '\n' + anchor, 1)
    print('已加社区选项加载')

# ---------- 6) 编辑时按已有代码回显级联 ----------
OLD_PREFILL = '''  editRegionPath.value = [row.province, row.city, row.district, row.street]
    .filter(Boolean)'''
NEW_PREFILL = '''  // 优先用代码回显，缺失时退回名称（兼容历史数据）
  const codes = [row.provinceCode, row.cityCode, row.districtCode, row.streetCode]
  editRegionPath.value = codes.every(Boolean)
    ? codes
    : []
  if (row.streetCode) {
    loadCommunities(row.streetCode)
  }'''
if OLD_PREFILL in s:
    s = s.replace(OLD_PREFILL, NEW_PREFILL, 1)
    print('编辑：按代码回显级联')

# ---------- 7) 表单与详情补代码字段 ----------
if 'provinceCode' not in s.split('const f = reactive')[1][:400]:
    s = s.replace('''  province: '', city: '', district: '', street: '', community: '',''',
                  '''  province: '', city: '', district: '', street: '', community: '',
  provinceCode: '', cityCode: '', districtCode: '', streetCode: '', communityCode: '',''',
                  1)
    print('表单已加代码字段')

if 'editForm.provinceCode' not in s.split('const editForm = reactive')[1][:300]:
    s = s.replace('''  parentId: null, community: '', address: '', sortNo: 1, remark: '' })''',
                  '''  parentId: null, community: '', address: '', sortNo: 1, remark: '',
  province: '', city: '', district: '', street: '',
  provinceCode: '', cityCode: '', districtCode: '', streetCode: '', communityCode: ''
})''', 1)
    print('编辑表单已加代码字段')

io.open(V, 'w', encoding='utf-8', newline='').write(s)
print('Orgs.vue 处理完成')
