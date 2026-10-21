# -*- coding: utf-8 -*-
"""人员档案四项修正：

1. 组织下拉选中「第N期小区」却总显示「第20期小区」
   —— 组织 ID 是 19 位雪花号，Number() 转换后精度丢失（> 2^53），多个 ID 变成同一个值。
   修法：下拉值与 v-model 一律用字符串，不转 Number。
2. 人员档案列表在姓名前增加「人员 ID」列，便于与保障档案/实名核验对应
3. 人员档案增加「实名状态」列；已通过的记录实名核验按钮置灰不可用
4. 保障档案 / 实名核验的查询框改为「人员 ID」（与列表新列对应）
   —— 保障档案接口补 personId 过滤参数
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'person')
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Persons.vue')


# ---------------- 后端：保障档案补 personId 过滤 ----------------
si = os.path.join(J, 'service', 'GuaranteeProfileService.java')
s = io.open(si, encoding='utf-8').read()
if 'Long personId' not in s:
    s = s.replace('String profileStatus, String keyword);',
                  'String profileStatus, String keyword, Long personId);', 1)
    io.open(si, 'w', encoding='utf-8', newline='').write(s)
    print('service 接口：已加 personId')

cp = os.path.join(J, 'controller', 'GuaranteeProfileController.java')
s = io.open(cp, encoding='utf-8').read()
if 'Long personId' not in s:
    s = s.replace('            @RequestParam(required = false) String keyword) {',
                  '''            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) Long personId) {''', 1)
    s = s.replace('profileStatus, keyword)', 'profileStatus, keyword, personId)')
    io.open(cp, 'w', encoding='utf-8', newline='').write(s)
    print('控制器：已加 personId')

ip = os.path.join(J, 'service', 'impl', 'GuaranteeProfileServiceImpl.java')
s = io.open(ip, encoding='utf-8').read()
if 'Long personId)' not in s:
    s = s.replace('String profileStatus, String keyword) {',
                  'String profileStatus, String keyword, Long personId) {', 1)
    s = s.replace('''                        .orderByDesc(PersonGuaranteeProfile::getId);''',
                  '''                        .eq(personId != null, PersonGuaranteeProfile::getPersonId, personId)
                        .orderByDesc(PersonGuaranteeProfile::getId);''', 1)
    io.open(ip, 'w', encoding='utf-8', newline='').write(s)
    print('实现：已加 personId 过滤')


# ---------------- 前端 ----------------
s = io.open(P, encoding='utf-8').read()
done = []

# 1) 组织下拉：ID 用字符串（避免 19 位数字精度丢失导致选项串位）
s = s.replace(':label="orgOptionLabel(o)" :value="Number(o.id)" />',
              ':label="orgOptionLabel(o)" :value="o.id" />', 1)
s = s.replace('''<el-option v-for="o in orgOptions" :key="o.id"
                   :label="orgOptionLabel(o)" :value="Number(o.id)" />''',
              '''<el-option v-for="o in orgOptions" :key="o.id"
                   :label="orgOptionLabel(o)" :value="String(o.id)" />''', 1)
s = s.replace('''  const hit = orgOptions.value.find((o) => Number(o.id) === Number(id))''',
              '''  const hit = orgOptions.value.find((o) => String(o.id) === String(id))''', 1)
# 编辑弹窗里的组织下拉同样改为字符串
s = s.replace(':label="o.orgName" :value="Number(o.id)" />', ':label="o.orgName" :value="String(o.id)" />')
if 'String(o.id)' in s:
    done.append('组织下拉字符串ID')

# 2) 人员档案列表：姓名前加「人员 ID」
s = s.replace('''        <el-table-column prop="personName" label="姓名" width="110" />''',
              '''        <el-table-column prop="id" label="人员ID" width="190" />
        <el-table-column prop="personName" label="姓名" width="110" />''', 1)
if 'label="人员ID"' in s:
    done.append('人员ID列')

# 3) 实名状态列 + 已通过时按钮置灰
s = s.replace('''        <el-table-column prop="phoneMask" label="手机号" width="140" />''',
              '''        <el-table-column prop="phoneMask" label="手机号" width="140" />
        <el-table-column label="实名状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.verifyStatus === 'VERIFIED' ? 'success' : 'info'">
              {{ enumLabel('verifyStatus', row.verifyStatus) }}
            </el-tag>
          </template>
        </el-table-column>''', 1)
s = s.replace('''<el-button link @click="openVerifyFor(row)">实名核验</el-button>''',
              '''<el-button link :disabled="row.verifyStatus === 'VERIFIED'"
                         @click="openVerifyFor(row)">实名核验</el-button>''', 1)
if 'verifyStatus' in s:
    done.append('实名状态列+置灰')

# 4) 保障档案 / 实名核验 查询框改人员ID
s = re.sub(r'<el-input v-model="gQuery\.keyword"[^/]*/>',
           '<el-input v-model="gQuery.personId" placeholder="人员ID" clearable\n'
           '                    style="width:220px" data-testid="profile-personid"\n'
           '                    @keyup.enter="loadProfiles" />', s, count=1)
s = re.sub(r'<el-input v-model="vQuery\.keyword"[^/]*/>',
           '<el-input v-model="vQuery.personId" placeholder="人员ID" clearable\n'
           '                    style="width:220px" data-testid="verify-personid"\n'
           '                    @keyup.enter="loadVerifies" />', s, count=1)
s = s.replace("const gQuery = reactive({ pageNum: 1, pageSize: 20, keyword: '' })",
              "const gQuery = reactive({ pageNum: 1, pageSize: 20, personId: '' })", 1)
s = s.replace("const vQuery = reactive({ pageNum: 1, pageSize: 20, keyword: '' })",
              "const vQuery = reactive({ pageNum: 1, pageSize: 20, personId: '' })", 1)
if 'gQuery.personId' in s and 'vQuery.personId' in s:
    done.append('查询改人员ID')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('前端已应用：', '、'.join(done) if done else '（无改动）')
