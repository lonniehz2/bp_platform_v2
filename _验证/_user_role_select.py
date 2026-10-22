# -*- coding: utf-8 -*-
"""新增用户：取消「用户类型」，改为直接选角色（可多选）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Rbac.vue')

s = io.open(P, encoding='utf-8').read()
changed = []

# 1) 模板：用户类型下拉 → 角色多选
m = re.search(r'<el-form-item label="用户类型">[\s\S]*?</el-form-item>', s)
if m:
    s = s[:m.start()] + '''<el-form-item label="角色" required>
          <el-select v-model="uf.roleIds" multiple filterable style="width:100%"
                     placeholder="选择角色（决定该账号能看到什么、能做什么）"
                     data-testid="user-roles">
            <el-option v-for="r in roles" :key="r.id"
                       :label="`${r.roleName}（${r.roleCode}）`" :value="String(r.id)" />
          </el-select></el-form-item>''' + s[m.end():]
    changed.append('模板')

# 2) 表单状态：userType → roleIds
s = re.sub(r"const uf = reactive\(\{[^}]*\}\)",
           "const uf = reactive({ username: '', password: '', realName: '', orgId: '', roleIds: [] })",
           s, count=1)
if 'roleIds: []' in s:
    changed.append('状态')

# 3) 提交：带上 roleIds
s = s.replace("await req.post('/rbac/users', { ...uf })",
              "await req.post('/rbac/users', { ...uf, roleIds: uf.roleIds || [] })", 1)

# 4) 校验：至少一个角色
s = s.replace("ElMessage.warning('请填写账号/密码/姓名/组织')",
              "ElMessage.warning('请填写账号/密码/姓名/组织，并至少选择一个角色')", 1)
if '至少选择一个角色' in s and "!uf.roleIds" not in s:
    s = s.replace("if (!uf.username || !uf.password || !uf.realName || !uf.orgId)",
                  "if (!uf.username || !uf.password || !uf.realName || !uf.orgId"
                  " || !(uf.roleIds && uf.roleIds.length))", 1)
    changed.append('校验')

# 5) 打开弹窗时清空角色选择
s = s.replace("Object.assign(uf, { username: '', password: '', realName: '', orgId: '', roleIds: [] })",
              "Object.assign(uf, { username: '', password: '', realName: '', orgId: '', roleIds: [] })")

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Rbac.vue 已改：', '、'.join(changed) if changed else '（未匹配）')
