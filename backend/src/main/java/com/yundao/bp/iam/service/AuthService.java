package com.yundao.bp.iam.service;

import com.yundao.bp.iam.dto.LoginCmd;
import com.yundao.bp.iam.dto.LoginVO;
import com.yundao.bp.iam.dto.MeVO;

/**
 * 认证服务（登录 / 登出 / 当前用户）。
 *
 * <p><b>令牌设计</b>：使用**不透明随机令牌**（32 字节 hex）落库到 `bp_iam_session`，
 * 而非 JWT。原因：会话表本身要求「强制下线 / 单设备登录」，
 * 不透明令牌可**即时撤销**，JWT 做不到（除非额外维护黑名单）。
 */
public interface AuthService {

    /** 登录，返回令牌。 */
    LoginVO login(LoginCmd cmd, String ip);

    /** 登出（当前令牌失效）。 */
    void logout(String token);

    /** 当前用户信息（含权限集）。 */
    MeVO me(Long userId);

    /** 按令牌加载登录用户（供拦截器调用）。 */
    com.yundao.bp.iam.security.LoginUser loadByToken(String token);

    /** 用户全部权限码（管理员返回 *）。 */
    java.util.Set<String> permissionCodes(Long userId);
}
