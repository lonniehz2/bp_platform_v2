# -*- coding: utf-8 -*-
"""用户角色可见性：
1. 用户列表批量带出角色名（避免 N+1）
2. 新增 GET /rbac/users/{userId}/roles（此前只有 POST，用户页看不到当前角色）

IamUser 增加非持久化字段 roleNames（字符串），前端直接展示。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iam')
C = os.path.join(J, 'controller', 'RbacController.java')
E = os.path.join(J, 'entity', 'IamUser.java')

# 1) 实体加非持久化字段
s = io.open(E, encoding='utf-8').read()
if 'roleNames' not in s:
    if 'TableField' not in s.split('\n')[0:20][0] and 'com.baomidou.mybatisplus.annotation.TableField' not in s:
        s = s.replace('import com.baomidou.mybatisplus.annotation.TableId;',
                      'import com.baomidou.mybatisplus.annotation.TableField;\n'
                      'import com.baomidou.mybatisplus.annotation.TableId;', 1)
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 非持久化：该用户的角色名（列表展示用，多个以顿号分隔） */
    @TableField(exist = false)
    private String roleNames;
''' + s[i:]
    io.open(E, 'w', encoding='utf-8', newline='').write(s)
    print('IamUser：已加 roleNames')

# 2) 控制器：列表批量补角色 + 新增 GET 单用户角色
c = io.open(C, encoding='utf-8').read()

old_list = '''        List<IamUser> list = userMapper.selectList(qw);
        list.forEach(u -> u.setPasswordHash(null));
        return R.ok(list);'''
new_list = '''        List<IamUser> list = userMapper.selectList(qw);
        list.forEach(u -> u.setPasswordHash(null));
        fillRoleNames(list);
        return R.ok(list);'''
if old_list in c:
    c = c.replace(old_list, new_list, 1)

helper = '''
    /** 批量补用户角色名（一次查关联表 + 角色表，避免逐条查询） */
    private void fillRoleNames(List<IamUser> users) {
        if (users == null || users.isEmpty()) {
            return;
        }
        List<Long> ids = new ArrayList<>();
        for (IamUser u : users) {
            ids.add(u.getId());
        }
        List<IamUserRole> links = userRoleMapper.selectList(
                new LambdaQueryWrapper<IamUserRole>()
                        .in(IamUserRole::getUserId, ids));
        if (links.isEmpty()) {
            return;
        }
        Set<Long> roleIds = new HashSet<>();
        for (IamUserRole l : links) {
            roleIds.add(l.getRoleId());
        }
        Map<Long, String> nameById = new HashMap<>();
        for (IamRole r : roleMapper.selectBatchIds(roleIds)) {
            nameById.put(r.getId(), r.getRoleName());
        }
        Map<Long, List<String>> byUser = new HashMap<>();
        for (IamUserRole l : links) {
            String nm = nameById.get(l.getRoleId());
            if (nm != null) {
                byUser.computeIfAbsent(l.getUserId(), k -> new ArrayList<>()).add(nm);
            }
        }
        for (IamUser u : users) {
            List<String> names = byUser.get(u.getId());
            u.setRoleNames(names == null ? "" : String.join("、", names));
        }
    }

    /** 某用户的角色列表（用户页回显用）。 */
    @GetMapping("/users/{userId}/roles")
    @RequirePerm("iam:user:list")
    public R<List<IamRole>> userRoles(@PathVariable Long userId) {
        List<IamUserRole> links = userRoleMapper.selectList(
                new LambdaQueryWrapper<IamUserRole>().eq(IamUserRole::getUserId, userId));
        if (links.isEmpty()) {
            return R.ok(List.of());
        }
        List<Long> ids = new ArrayList<>();
        for (IamUserRole l : links) {
            ids.add(l.getRoleId());
        }
        return R.ok(roleMapper.selectBatchIds(ids));
    }
'''
anchor = '    /** 给用户分配角色。 */'
if 'userRoles(@PathVariable Long userId)' not in c and anchor in c:
    c = c.replace(anchor, helper + '\n' + anchor, 1)

# 需要的集合类导入
for imp in ['import java.util.ArrayList;', 'import java.util.HashMap;',
            'import java.util.HashSet;', 'import java.util.Map;', 'import java.util.Set;']:
    if imp not in c:
        c = c.replace('import java.time.LocalDateTime;',
                      'import java.time.LocalDateTime;\n' + imp, 1)

io.open(C, 'w', encoding='utf-8', newline='').write(c)
print('RbacController：列表补角色 + GET userRoles')
