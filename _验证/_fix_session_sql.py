# -*- coding: utf-8 -*-
"""修正 IamSessionMapper 的 SQL（bp_iam_session 无 is_deleted 列）"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp\iam\mapper\IamSessionMapper.java'
content = '''package com.yundao.bp.iam.mapper;

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
     * 此时没有 tenant_id 可用于过滤；且令牌全局唯一，
     * 会话记录里的 tenant_id 才是<b>权威来源</b>（不由客户端指定，防跨租户）。
     *
     * <p>注意：bp_iam_session 表<b>没有</b> is_deleted 列（会话用 status 表达生命周期）。
     */
    @InterceptorIgnore(tenantLine = "true")
    @Select("SELECT * FROM bp_iam_session WHERE token_id = #{token} ORDER BY id DESC LIMIT 1")
    IamSession selectByTokenIgnoreTenant(@Param("token") String token);
}
'''
io.open(p, 'w', encoding='utf-8').write(content)
print('已重写 IamSessionMapper（去掉 is_deleted 条件）')
