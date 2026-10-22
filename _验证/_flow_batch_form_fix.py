# -*- coding: utf-8 -*-
"""修正配租「新建批次」表单：按 BatchCreateCmd 的真实必填项组织。

必填：batchName、orgId、securityType、batchType(LOTTERY|SELECT|DIRECT|SUPPLEMENT)
可选：houseIds、signupStart/End、lotteryTime、selectStart/End、notaryInfo、remark
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Allocations.vue')

s = io.open(P, encoding='utf-8').read()

new_dialog = '''    <!-- 新建批次 -->
    <el-dialog v-model="batchCreateVisible" title="新建配租批次" width="620px">
      <el-form :model="bf" label-width="110px">
        <el-form-item label="批次名称" required>
          <el-input v-model="bf.batchName" placeholder="如：2026 年第一批公租房配租" />
        </el-form-item>
        <el-form-item label="项目组织" required>
          <el-select v-model="bf.orgId" filterable style="width:100%"
                     placeholder="选择所属小区/项目">
            <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName" :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="保障类型" required>
            <el-select v-model="bf.securityType" style="width:100%">
              <el-option label="公租房" value="PUBLIC" />
              <el-option label="经适房" value="AFFORDABLE" />
              <el-option label="人才房" value="TALENT" />
              <el-option label="廉租房" value="LOW_RENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="批次类型" required>
            <el-select v-model="bf.batchType" style="width:100%">
              <el-option label="摇号配租" value="LOTTERY" />
              <el-option label="选房配租" value="SELECT" />
              <el-option label="直接配租" value="DIRECT" />
              <el-option label="补充配租" value="SUPPLEMENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="报名开始">
            <el-date-picker v-model="bf.signupStart" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="报名结束">
            <el-date-picker v-model="bf.signupEnd" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="摇号时间">
            <el-date-picker v-model="bf.lotteryTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="房源 ID">
            <el-input v-model="bf.houseIdsText" type="textarea" :rows="2"
                      placeholder="可空；创建后也能用行内「加房源」补充，多个用逗号分隔" />
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="公证信息">
            <el-input v-model="bf.notaryInfo" placeholder="可空，如公证处与公证号" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="batchCreateVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateBatch">创建</el-button>
      </template>
    </el-dialog>
'''

# 替换旧弹窗
m = re.search(r'    <!-- 新建批次 -->[\s\S]*?</el-dialog>\n', s)
if m:
    s = s[:m.start()] + new_dialog + s[m.end():]
    print('弹窗已替换')
else:
    print('未找到旧弹窗')

# 脚本：扩展 bf 与提交逻辑，加载组织
old_state = re.search(r"const bf = reactive\(\{[^}]*\}\)", s)
if old_state:
    s = s[:old_state.start()] + (
        "const bf = reactive({ batchName: '', orgId: '', securityType: 'PUBLIC',\n"
        "  batchType: 'LOTTERY', signupStart: '', signupEnd: '', lotteryTime: '',\n"
        "  houseIdsText: '', notaryInfo: '' })\nconst orgOptions = ref([])") + s[old_state.end():]

old_open = re.search(r"function openBatchCreate\(\) \{[\s\S]*?\n\}", s)
if old_open:
    s = s[:old_open.start()] + '''async function openBatchCreate() {
  Object.assign(bf, { batchName: '', orgId: '', securityType: 'PUBLIC', batchType: 'LOTTERY',
    signupStart: '', signupEnd: '', lotteryTime: '', houseIdsText: '', notaryInfo: '' })
  batchCreateVisible.value = true
  if (!orgOptions.value.length) {
    try {
      const list = await req.get('/orgs')
      orgOptions.value = (list || []).map((o) => ({ id: o.id, orgName: o.orgName }))
    } catch (e) { /* 组织加载失败不阻断 */ }
  }
}''' + s[old_open.end():]

old_create = re.search(r"async function doCreateBatch\(\) \{[\s\S]*?\n\}", s)
if old_create:
    s = s[:old_create.start()] + '''async function doCreateBatch() {
  if (!bf.batchName) { ElMessage.warning('请填写批次名称'); return }
  if (!bf.orgId) { ElMessage.warning('请选择项目组织'); return }
  const ids = (bf.houseIdsText || '').split(/[,，\\s]+/).map((x) => x.trim()).filter(Boolean)
  saving.value = true
  try {
    await req.post('/allocation/batches', {
      batchName: bf.batchName,
      orgId: bf.orgId,
      securityType: bf.securityType,
      batchType: bf.batchType,
      signupStart: bf.signupStart || null,
      signupEnd: bf.signupEnd || null,
      lotteryTime: bf.lotteryTime || null,
      houseIds: ids.length ? ids : null,
      notaryInfo: bf.notaryInfo || null
    })
    ElMessage.success('批次已创建')
    batchCreateVisible.value = false
    load()
  } finally { saving.value = false }
}''' + s[old_create.end():]

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Allocations.vue 已更新为完整批次表单')
