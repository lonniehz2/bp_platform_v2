# -*- coding: utf-8 -*-
import io
import os

BASE = r'..\backend\src\main\java\com\yundao\bp\iam'

# 1) 新增 Cmd
p = os.path.join(BASE, 'dto/ChangePasswordCmd.java')
io.open(p, 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChangePasswordCmd(
        @NotBlank(message = "原密码不能为空") String oldPassword,
        @NotBlank(message = "新密码不能为空")
        @Size(min = 10, max = 64, message = "新密码至少 10 位") String newPassword
) {
}
''')

# 2) MeVO 增加 mustChangePassword
p = os.path.join(BASE, 'dto/MeVO.java')
s = io.open(p, encoding='utf-8').read()
if 'mustChangePassword' not in s:
    s = s.replace('        List<Long> roleIds', '        List<Long> roleIds,\n        Boolean mustChangePassword', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)

# 3) AuthService 接口
p = os.path.join(BASE, 'service/AuthService.java')
s = io.open(p, encoding='utf-8').read()
if 'changePassword' not in s:
    idx = s.rfind('}')
    s = s[:idx] + '''
    /** 业务用户修改密码（首次登录/重置后强制）。 */
    void changePassword(Long userId, String oldPassword, String newPassword);
''' + s[idx:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)

# 4) AuthServiceImpl: me 增加字段 + 改密实现
p = os.path.join(BASE, 'service/impl/AuthServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'mustChangePassword' not in s:
    s = s.replace('''                new ArrayList<>(perms), roleIds);''',
                  '''                new ArrayList<>(perms), roleIds,
                user.getMustChangePassword() != null && user.getMustChangePassword() == 1);''', 1)
    idx = s.rfind('}')
    s = s[:idx] + '''
    @Override
    public void changePassword(Long userId, String oldPassword, String newPassword) {
        IamUser u = userMapper.selectById(userId);
        if (u == null) {
            throw BizException.notFound("用户");
        }
        if (!hasher.verify(oldPassword, u.getPasswordHash())) {
            throw new BizException(ErrorCode.PARAM_INVALID, "原密码不正确");
        }
        if (newPassword == null || newPassword.length() < 10) {
            throw new BizException(ErrorCode.PARAM_INVALID, "新密码至少 10 位");
        }
        u.setPasswordHash(hasher.hash(newPassword));
        u.setMustChangePassword(0);
        u.setPwdUpdateTime(LocalDateTime.now());
        u.setUpdateTime(LocalDateTime.now());
        userMapper.updateById(u);
    }
''' + s[idx:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('backend password change added')
