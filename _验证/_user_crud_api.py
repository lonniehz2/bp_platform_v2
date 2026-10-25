# -*- coding: utf-8 -*-
"""用户管理：补详情 / 编辑 / 删除 / 启停接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
IAM = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iam')

P = os.path.join(IAM, 'controller', 'RbacController.java')
s = io.open(P, encoding='utf-8').read()

if '/users/{userId}/status' in s:
    print('已存在用户接口')
    raise SystemExit(0)

ADD = '''
    /** 用户详情。 */
    @com.yundao.bp.iam.security.RequirePerm("sys:rbac:view")
    @GetMapping("/users/{userId}")
    public R<com.yundao.bp.iam.entity.IamUser> userDetail(@PathVariable Long userId) {
        com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(userId);
        if (u == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("用户");
        }
        return R.ok(u);
    }

    /** 编辑用户（姓名/手机/邮箱/所属组织）。 */
    @com.yundao.bp.iam.security.RequirePerm("sys:rbac:view")
    @PutMapping("/users/{userId}")
    public R<com.yundao.bp.iam.entity.IamUser> updateUser(
            @PathVariable Long userId,
            @RequestBody java.util.Map<String, Object> body) {
        com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(userId);
        if (u == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("用户");
        }
        setIfPresent(u::setRealName, body.get("realName"));
        setIfPresent(u::setPhone, body.get("phone"));
        setIfPresent(u::setEmail, body.get("email"));
        Object orgId = body.get("orgId");
        if (orgId != null && !String.valueOf(orgId).isBlank()) {
            u.setOrgId(Long.valueOf(String.valueOf(orgId)));
        }
        u.setUpdateTime(java.time.LocalDateTime.now());
        userMapper.updateById(u);
        return R.ok(u);
    }

    /** 启用 / 停用用户。 */
    @com.yundao.bp.iam.security.RequirePerm("sys:rbac:view")
    @PostMapping("/users/{userId}/status")
    public R<com.yundao.bp.iam.entity.IamUser> changeUserStatus(
            @PathVariable Long userId, @RequestBody java.util.Map<String, String> body) {
        com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(userId);
        if (u == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("用户");
        }
        String status = body == null ? null : body.get("status");
        if (status == null || !java.util.List.of("ENABLED", "DISABLED", "LOCKED")
                .contains(status)) {
            throw com.yundao.bp.common.exception.BizException
                    .paramInvalid("状态只能是 ENABLED / DISABLED / LOCKED");
        }
        u.setUserStatus(status);
        u.setUpdateTime(java.time.LocalDateTime.now());
        userMapper.updateById(u);
        return R.ok(u);
    }

    /** 删除用户（逻辑删除）。 */
    @com.yundao.bp.iam.security.RequirePerm("sys:rbac:view")
    @DeleteMapping("/users/{userId}")
    public R<Void> deleteUser(@PathVariable Long userId) {
        com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(userId);
        if (u == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("用户");
        }
        if ("admin".equalsIgnoreCase(u.getUsername())) {
            throw com.yundao.bp.common.exception.BizException
                    .stateConflict("内置管理员账号不可删除");
        }
        userMapper.deleteById(userId);
        return R.ok();
    }

    private void setIfPresent(java.util.function.Consumer<String> setter, Object v) {
        if (v != null && !String.valueOf(v).isBlank()) {
            setter.accept(String.valueOf(v));
        }
    }
'''

i = s.rstrip().rfind('}')
s = s[:i] + ADD + s[i:]

if 'DeleteMapping' not in s:
    s = s.replace('import org.springframework.web.bind.annotation.PutMapping;',
                  'import org.springframework.web.bind.annotation.PutMapping;\n'
                  'import org.springframework.web.bind.annotation.DeleteMapping;')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('RbacController：已加用户详情/编辑/状态/删除')
