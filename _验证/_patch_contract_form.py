# -*- coding: utf-8 -*-
"""合同表单：ID 输入改为名称搜索；选房源带出空间/地址/面积。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    if old not in s:
        print('未匹配:', old[:60].replace('\n', ' '))
        return
    s = s.replace(old, new, 1)


# 表单字段替换
rep('''          <el-col :span="12"><el-form-item label="出租组织ID" required>
            <el-input v-model="c.orgId" data-testid="c-org-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="出租方组织ID" required>
            <el-input v-model="c.lessorOrgId" data-testid="c-lessor-org-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="承租人ID" required>
            <el-input v-model="c.lesseePersonId" data-testid="c-lessee-id" /></el-form-item></el-col>''',
    '''          <el-col :span="12"><el-form-item label="出租组织" required>
            <OrgSelect v-model="c.orgId" testid="c-org-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="出租方组织" required>
            <OrgSelect v-model="c.lessorOrgId" testid="c-lessor-org-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="承租人" required>
            <PersonPicker v-model="c.lesseePersonId" width="100%" testid="c-lessee-id" /></el-form-item></el-col>''')

rep('''          <el-col :span="12"><el-form-item label="房源ID" required>
            <el-input v-model="c.houseId" data-testid="c-house-id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="空间ID" required>
            <el-input v-model="c.spaceId" data-testid="c-space-id" /></el-form-item></el-col>''',
    '''          <el-col :span="12"><el-form-item label="房源" required>
            <HouseSelect v-model="c.houseId" :org-id="c.orgId" testid="c-house-id"
                         @picked="onHousePicked" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="空间">
            <el-input :model-value="spaceLabel" disabled
                      placeholder="选择房源后自动带出" data-testid="c-space-id" /></el-form-item></el-col>''')

# 校验提示文案
rep("if (!c.orgId) missing.push('出租组织ID')", "if (!c.orgId) missing.push('出租组织')")
rep("if (!c.lessorOrgId) missing.push('出租方组织ID')", "if (!c.lessorOrgId) missing.push('出租方组织')")
rep("if (!c.lesseePersonId) missing.push('承租人ID')", "if (!c.lesseePersonId) missing.push('承租人')")
rep("if (!c.houseId) missing.push('房源ID')", "if (!c.houseId) missing.push('房源')")
rep("if (!c.spaceId) missing.push('空间ID')", "if (!c.spaceId) missing.push('空间（选择房源自动带出）')")

# 引入组件与状态
rep('''import PersonPicker from '@/components/PersonPicker.vue' ''',
    '''import PersonPicker from '@/components/PersonPicker.vue'
import OrgSelect from '@/components/OrgSelect.vue'
import HouseSelect from '@/components/HouseSelect.vue' ''')

rep('''const c = reactive({ contractType: 'PUBLIC_RENTAL', orgId: 1, lessorOrgId: 1, lesseePersonId: null,''',
    '''const spaceLabel = ref('')

/** 选房源：带出空间/地址/面积/租金标准 */
function onHousePicked(h) {
  if (!h) return
  c.spaceId = h.spaceId
  spaceLabel.value = h.spaceName || (h.spaceId ? '空间 ' + h.spaceId : '')
  if (!c.houseAddress) c.houseAddress = h.houseAddress || h.houseName || ''
  if (!c.houseArea) c.houseArea = h.area
  if (!c.rentPrice && h.rentStandard) c.rentPrice = h.rentStandard
}

const c = reactive({ contractType: 'PUBLIC_RENTAL', orgId: 1, lessorOrgId: 1, lesseePersonId: null,''')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('Contracts.vue 已更新')
