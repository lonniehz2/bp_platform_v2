# -*- coding: utf-8 -*-
"""修正 RBAC 编译错误"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# 1) IamPermission 补 createTime
p1 = os.path.join(BASE, r'iam\entity\IamPermission.java')
s1 = io.open(p1, encoding='utf-8').read()
if 'createTime' not in s1:
    s1 = s1.replace('    private String status;',
                    '    private String status;\n    private java.time.LocalDateTime createTime;')
    io.open(p1, 'w', encoding='utf-8').write(s1)
    print('  ✓ IamPermission 补 createTime')

# 2) 拦截器改用 R.fail
p2 = os.path.join(BASE, r'iam\security\AuthInterceptor.java')
s2 = io.open(p2, encoding='utf-8').read()
old = '''    private static void reject(HttpServletResponse resp, int httpStatus, ErrorCode code,
                               String msg) throws Exception {
        resp.setStatus(httpStatus);
        resp.setContentType("application/json;charset=UTF-8");
        R<Void> body = new R<>(code.getCode(), msg, null, System.currentTimeMillis());
        resp.getOutputStream().write(
                JSON.writeValueAsString(body).getBytes(StandardCharsets.UTF_8));
    }'''
new = '''    private static void reject(HttpServletResponse resp, int httpStatus, ErrorCode code,
                               String msg) throws Exception {
        resp.setStatus(httpStatus);
        resp.setContentType("application/json;charset=UTF-8");
        R<Void> body = R.fail(code, msg);
        resp.getOutputStream().write(
                JSON.writeValueAsString(body).getBytes(StandardCharsets.UTF_8));
    }'''
assert old in s2
s2 = s2.replace(old, new, 1)
io.open(p2, 'w', encoding='utf-8').write(s2)
print('  ✓ 拦截器改用 R.fail')

# 3) 拦截器里的错误码换成语义正确的 UNAUTHORIZED / FORBIDDEN
s2 = io.open(p2, encoding='utf-8').read()
s2 = s2.replace('''            reject(resp, 401, ErrorCode.TENANT_CONTEXT_MISSING,
                    "未登录或登录已过期，请重新登录");''',
                '''            reject(resp, 401, ErrorCode.UNAUTHORIZED,
                    "未登录或登录已过期，请重新登录");''')
s2 = s2.replace('''            reject(resp, 403, ErrorCode.PARAM_INVALID,
                    "无操作权限（需要权限：" + perm.value() + "）");''',
                '''            reject(resp, 403, ErrorCode.FORBIDDEN,
                    "无操作权限（需要权限：" + perm.value() + "）");''')
io.open(p2, 'w', encoding='utf-8').write(s2)
print('  ✓ 错误码改为 UNAUTHORIZED / FORBIDDEN')
