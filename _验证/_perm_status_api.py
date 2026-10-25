# -*- coding: utf-8 -*-
"""权限：补启用/停用接口（角色已有 PUT、字典与开放平台已有 status 接口）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iam',
                 'controller', 'RbacController.java')
s = io.open(P, encoding='utf-8').read()

if '/permissions/{permId}/status' in s:
    print('已存在权限状态接口')
    raise SystemExit(0)

ADD = '''
    /** 启用 / 停用权限码。 */
    @PostMapping("/permissions/{permId}/status")
    @RequirePerm("iam:perm:list")
    public R<IamPermission> changePermStatus(
            @PathVariable Long permId, @RequestBody java.util.Map<String, String> body) {
        IamPermission p = permMapper.selectById(permId);
        if (p == null) {
            throw BizException.notFound("权限");
        }
        String status = body == null ? null : body.get("status");
        if (status == null || !java.util.List.of("ENABLED", "DISABLED").contains(status)) {
            throw BizException.paramInvalid("状态只能是 ENABLED / DISABLED");
        }
        p.setStatus(status);
        permMapper.updateById(p);
        return R.ok(p);
    }
'''

i = s.rstrip().rfind('}')
s = s[:i] + ADD + s[i:]
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('RbacController：已加权限状态接口')
