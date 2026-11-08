import io
p=r'src\main\java\com\yundao\platform\service\AuthService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public void changePassword(ChangePasswordCmd cmd) {
        UserContext.Principal principal = UserContext.require();
        if (cmd.oldPassword() == null || cmd.newPassword() == null || cmd.newPassword().length() < 6) {
            throw BizException.param("新密码至少 6 位");
        }
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select password_hash passwordHash from bp_user where id=? and tenant_id=? and is_deleted=0",
                principal.userId(), principal.tenantId());
        if (rows.isEmpty()) {
            throw BizException.notFound("用户不存在");
        }
        String stored = String.valueOf(rows.get(0).get("passwordHash"));
        boolean matched = stored.startsWith("pbkdf2$")
                ? LegacyPasswordHasher.verify(cmd.oldPassword(), stored)
                : encoder.matches(cmd.oldPassword(), stored);
        if (!matched) {
            throw BizException.param("原密码错误");
        }
        jdbc.update("update bp_user set password_hash=?, update_time=now() where id=?",
                encoder.encode(cmd.newPassword()), principal.userId());
    }

    public record ChangePasswordCmd(String oldPassword, String newPassword) {
    }

'''
marker='    public record LoginCmd('
if marker not in s: raise SystemExit('marker missing')
s=s.replace(marker, insert+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('change password service')
