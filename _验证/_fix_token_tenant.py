# -*- coding: utf-8 -*-
"""修正：令牌校验绕过租户拦截（令牌全局唯一，且租户由会话记录决定）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# 1) IamSessionMapper 增加绕过租户的按令牌查询
p1 = os.path.join(BASE, r'iam\mapper\IamSessionMapper.java')
io.open(p1, 'w', encoding='utf-8').write('''package com.yundao.bp.iam.mapper;

import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.iam.entity.IamSession;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface IamSessionMapper extends BaseMapper<IamSession> {

    /**
     * 按令牌查询会话（<b>绕过租户过滤</b>）。
     *
     * <p>为什么必须绕过：认证发生在租户上下文建立<b>之前</b>，
     * 此时还没有 tenant_id 可用于过滤；且令牌本身全局唯一，
     * 会话记录里的 tenant_id 才是**权威来源**（不由客户端指定，防跨租户）。
     */
    @InterceptorIgnore(tenantLine = "true")
    @Select("SELECT * FROM bp_iam_session WHERE token_id = #{token} AND is_deleted = 0 "
            + "ORDER BY id DESC LIMIT 1")
    IamSession selectByTokenIgnoreTenant(@Param("token") String token);
}
''')
print('  ✓ IamSessionMapper 增加绕过租户的令牌查询')

# 2) AuthServiceImpl：用新方法 + 用会话里的租户建立上下文
p2 = os.path.join(BASE, r'iam\service\impl\AuthServiceImpl.java')
s = io.open(p2, encoding='utf-8').read()

old_find = '''    private IamSession findByToken(String token) {
        if (token == null || token.isBlank()) {
            return null;
        }
        return sessionMapper.selectOne(new LambdaQueryWrapper<IamSession>()
                .eq(IamSession::getTokenId, token)
                .last("LIMIT 1"));
    }'''
new_find = '''    private IamSession findByToken(String token) {
        if (token == null || token.isBlank()) {
            return null;
        }
        // 绕过租户过滤：认证时尚无租户上下文，且令牌全局唯一
        return sessionMapper.selectByTokenIgnoreTenant(token);
    }'''
assert old_find in s
s = s.replace(old_find, new_find, 1)

# loadByToken：先用会话里的租户建立上下文，再查用户与权限
old_load = '''        IamSession s = findByToken(token);
        if (s == null || !"ACTIVE".equals(s.getStatus())) {
            return null;
        }
        if (s.getExpireTime() != null && s.getExpireTime().isBefore(LocalDateTime.now())) {
            s.setStatus("EXPIRED");
            sessionMapper.updateById(s);
            return null;
        }
        IamUser user = userMapper.selectById(s.getUserId());'''
new_load = '''        IamSession s = findByToken(token);
        if (s == null || !"ACTIVE".equals(s.getStatus())) {
            return null;
        }
        // ⭐ 以会话记录里的租户为准建立上下文（权威来源，非客户端传入）
        TenantContext.set(TenantInfo.of(s.getTenantId(), s.getUserId()));

        if (s.getExpireTime() != null && s.getExpireTime().isBefore(LocalDateTime.now())) {
            s.setStatus("EXPIRED");
            sessionMapper.updateById(s);
            return null;
        }
        IamUser user = userMapper.selectById(s.getUserId());'''
assert old_load in s
s = s.replace(old_load, new_load, 1)

io.open(p2, 'w', encoding='utf-8').write(s)
print('  ✓ loadByToken 用会话租户建立上下文')
