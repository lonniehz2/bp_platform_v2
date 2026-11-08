import io
p=r'src\main\java\com\yundao\platform\service\PermissionService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    public void require(String permission) {
        UserContext.Principal principal = UserContext.require();
        List<String> roles = jdbc.queryForList(''','''    public java.util.Set<String> permissions() {
        UserContext.Principal principal = UserContext.require();
        List<String> roles = jdbc.queryForList(
                "select r.role_code roleCode from bp_user_role ur join bp_role r on r.id=ur.role_id "
                        + "where ur.tenant_id=? and ur.user_id=? and r.role_status='ENABLED'",
                String.class, principal.tenantId(), principal.userId());
        java.util.Set<String> out = new java.util.LinkedHashSet<>();
        for (String role : roles) out.addAll(grants(role));
        return out;
    }

    public void require(String permission) {
        UserContext.Principal principal = UserContext.require();
        List<String> roles = jdbc.queryForList(''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\AuthController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }''','''    private final AuthService authService;
    private final com.yundao.platform.service.PermissionService permissionService;

    public AuthController(AuthService authService,
                          com.yundao.platform.service.PermissionService permissionService) {
        this.authService = authService;
        this.permissionService = permissionService;
    }''')
s=s.replace('''    @GetMapping("/menus")''','''    @GetMapping("/permissions")
    public R<java.util.List<String>> permissions() {
        return R.ok(java.util.List.copyOf(permissionService.permissions()));
    }

    @GetMapping("/menus")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('permissions endpoint')
