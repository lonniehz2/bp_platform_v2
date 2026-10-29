# -*- coding: utf-8 -*-
import io

# 1) 忽略表
p = r'..\backend\src\main\java\com\yundao\bp\common\config\MybatisTenantConfig.java'
s = io.open(p, encoding='utf-8').read()
if 'bp_iam_platform_operator' not in s:
    s = s.replace('"bp_open_call_log"', '''"bp_open_call_log",
            // 平台运营台（跨平台表，无 tenant_id）
            "bp_iam_platform_operator", "bp_iam_platform_operator_session",
            "bp_iam_platform_audit", "bp_iam_tenant_branding", "bp_sys_platform_seq"''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('ignore tables added')

# 2) 拦截器放行运营台/公开品牌
p = r'..\backend\src\main\java\com\yundao\bp\iam\security\AuthInterceptor.java'
s = io.open(p, encoding='utf-8').read()
if 'platform-admin' not in s:
    s = s.replace('''        if (path.startsWith("/api/callback/")) {
            return true;
        }''', '''        if (path.startsWith("/api/callback/")) {
            return true;
        }
        // 平台运营台：独立令牌（X-Operator-Token），由控制器自行校验
        if (path.startsWith("/api/v1/platform-admin/")) {
            return true;
        }
        // 登录前品牌信息
        if (path.startsWith("/api/v1/public/")) {
            return true;
        }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('interceptor whitelist added')

# 3) 业务登录检查平台状态
p = r'..\backend\src\main\java\com\yundao\bp\iam\service\impl\AuthServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
if '平台已停用' not in s:
    s = s.replace('''        if (!"ENABLED".equals(user.getStatus())) {''', '''        if (tenantMapper != null) {
            com.yundao.bp.iam.entity.IamTenant tenantRow = tenantMapper.selectOne(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                            <com.yundao.bp.iam.entity.IamTenant>()
                            .eq(com.yundao.bp.iam.entity.IamTenant::getTenantCode,
                                    user.getTenantId())
                            .last("LIMIT 1"));
            if (tenantRow == null
                    || (tenantRow.getDeleted() != null && tenantRow.getDeleted() == 1)) {
                throw new BizException(ErrorCode.FORBIDDEN, "平台不存在或已归档");
            }
            if (!"ENABLED".equals(tenantRow.getStatus())) {
                throw new BizException(ErrorCode.FORBIDDEN, "平台已停用，请联系平台运营");
            }
        }
        if (!"ENABLED".equals(user.getStatus())) {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('tenant login check added')

# 4) 平台侧只允许改名
p = r'..\backend\src\main\java\com\yundao\bp\iam\service\PlatformInfoService.java'
s = io.open(p, encoding='utf-8').read()
s = s.replace('''        t.setTenantName(cmd.tenantName());
        if (cmd.tenantType() != null && !cmd.tenantType().isBlank()) {
            t.setTenantType(cmd.tenantType());
        }
        t.setRegionCode(cmd.regionCode());
        if (cmd.status() != null && !cmd.status().isBlank()) {
            t.setStatus(cmd.status());
        }''', '''        // 平台侧仅允许修改名称；区域/类型/状态由运营超管控制
        t.setTenantName(cmd.tenantName());''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('platform info name-only')
