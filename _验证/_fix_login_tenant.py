# -*- coding: utf-8 -*-
"""修正：登录接口需先建立租户上下文"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# 1) LoginCmd 增加 tenantId
p1 = os.path.join(BASE, r'iam\dto\LoginCmd.java')
s1 = io.open(p1, encoding='utf-8').read()
if 'tenantId' not in s1:
    s1 = s1.replace('''        @NotBlank(message = "登录名不能为空")
        String username,''',
                    '''        /**
         * 租户ID。
         *
         * <p>登录时尚未建立租户上下文，必须先由请求指定，否则租户拦截器会拒绝
         * （写入会话/更新登录信息都需 tenant_id）。多租户下登录名仅在租户内唯一。
         */
        String tenantId,

        @NotBlank(message = "登录名不能为空")
        String username,''')
    io.open(p1, 'w', encoding='utf-8').write(s1)
    print('  ✓ LoginCmd 增加 tenantId')

# 2) AuthServiceImpl.login 开头建立租户上下文
p2 = os.path.join(BASE, r'iam\service\impl\AuthServiceImpl.java')
s2 = io.open(p2, encoding='utf-8').read()
if 'cmd.tenantId()' not in s2:
    s2 = s2.replace('''    public LoginVO login(LoginCmd cmd, String ip) {
        IamUser user = userMapper.selectOne(new LambdaQueryWrapper<IamUser>()''',
                    '''    public LoginVO login(LoginCmd cmd, String ip) {
        // ⭐ 登录时还没有租户上下文，必须先建立，否则会话写入/登录信息更新会被租户拦截器拒绝
        String tenant = (cmd.tenantId() == null || cmd.tenantId().isBlank())
                ? "350600" : cmd.tenantId().trim();
        TenantContext.set(TenantInfo.of(tenant, null));

        IamUser user = userMapper.selectOne(new LambdaQueryWrapper<IamUser>()''')
    # 导入
    s2 = s2.replace('import com.yundao.bp.common.id.SnowflakeIdGenerator;',
                    'import com.yundao.bp.common.id.SnowflakeIdGenerator;\n'
                    'import com.yundao.bp.common.tenant.TenantContext;\n'
                    'import com.yundao.bp.common.tenant.TenantInfo;', 1)
    # 登录成功后把上下文切到该用户
    s2 = s2.replace('''        String token = hasher.newToken();
        LocalDateTime now = LocalDateTime.now();''',
                    '''        // 以用户真实租户为准（防止跨租户登录）
        TenantContext.set(TenantInfo.of(user.getTenantId(), user.getId()));

        String token = hasher.newToken();
        LocalDateTime now = LocalDateTime.now();''')
    io.open(p2, 'w', encoding='utf-8').write(s2)
    print('  ✓ 登录流程先建立租户上下文')

# 3) 页面登录请求带上 tenantId
p3 = os.path.join(BASE, r'..\..\..\resources\static\index.html')
p3 = os.path.normpath(os.path.join(
    BASE, r'..\..\..\..\..\resources\static\index.html'))
if not os.path.exists(p3):
    p3 = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s3 = io.open(p3, encoding='utf-8').read()
if "tenantId" not in s3:
    s3 = s3.replace(
        "const body = JSON.stringify({ username: username, password: password, deviceType: 'WEB' });",
        "const body = JSON.stringify({ tenantId: '350600', username: username, "
        "password: password, deviceType: 'WEB' });")
    io.open(p3, 'w', encoding='utf-8').write(s3)
    print('  ✓ 页面登录带上租户ID')
else:
    print('  - 页面已含 tenantId')
