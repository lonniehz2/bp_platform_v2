import io
p=r'src\main\java\com\yundao\platform\config\PermissionInterceptor.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''        UserContext.Principal principal = UserContext.get();
        if (principal == null) {
            return deny(response, "BP40100", "未登录或登录已过期", 401);
        }''','''        UserContext.Principal principal = UserContext.get();
        if (principal == null) {
            return deny(response, "BP40100", "未登录或登录已过期", 401);
        }
        if (!"GET".equalsIgnoreCase(request.getMethod())
                && !"HEAD".equalsIgnoreCase(request.getMethod())
                && !"OPTIONS".equalsIgnoreCase(request.getMethod())) {
            Long auditor = jdbc.queryForObject(
                    "select count(*) from bp_user_role ur join bp_role r on r.id=ur.role_id "
                            + "where ur.tenant_id=? and ur.user_id=? and r.role_code='AUDITOR'",
                    Long.class, TenantContext.require(), principal.userId());
            if (auditor != null && auditor > 0) {
                return deny(response, "BP40301", "只读角色不能执行写操作", 403);
            }
        }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('readonly guard')
