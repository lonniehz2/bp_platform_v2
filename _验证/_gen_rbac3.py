# -*- coding: utf-8 -*-
"""生成 RBAC：登录服务 + 权限拦截器 + 接口 + 初始化数据"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

# ==================== AuthService ====================
F['iam/service/AuthService.java'] = '''package com.yundao.bp.iam.service;

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
'''

# ==================== DTO ====================
F['iam/dto/LoginCmd.java'] = '''package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * 登录请求。
 */
public record LoginCmd(

        @NotBlank(message = "登录名不能为空")
        String username,

        @NotBlank(message = "密码不能为空")
        String password,

        /** WEB / APP / MINIAPP / SCREEN */
        String deviceType,

        String deviceId
) {
}
'''

F['iam/dto/LoginVO.java'] = '''package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

/**
 * 登录结果。
 */
public record LoginVO(
        String token,
        Long userId,
        String username,
        String realName,
        String tenantId,
        Long orgId,
        Boolean admin,
        LocalDateTime expireTime
) {
}
'''

F['iam/dto/MeVO.java'] = '''package com.yundao.bp.iam.dto;

import java.util.List;

/**
 * 当前用户信息。
 */
public record MeVO(
        Long userId,
        String username,
        String realName,
        String tenantId,
        Long orgId,
        String userType,
        Boolean admin,
        List<String> permissions,
        List<Long> roleIds
) {
}
'''

F['iam/service/impl/AuthServiceImpl.java'] = '''package com.yundao.bp.iam.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.iam.dto.LoginCmd;
import com.yundao.bp.iam.dto.LoginVO;
import com.yundao.bp.iam.dto.MeVO;
import com.yundao.bp.iam.entity.IamPermission;
import com.yundao.bp.iam.entity.IamRole;
import com.yundao.bp.iam.entity.IamRolePermission;
import com.yundao.bp.iam.entity.IamSession;
import com.yundao.bp.iam.entity.IamUser;
import com.yundao.bp.iam.entity.IamUserRole;
import com.yundao.bp.iam.mapper.IamPermissionMapper;
import com.yundao.bp.iam.mapper.IamRoleMapper;
import com.yundao.bp.iam.mapper.IamRolePermissionMapper;
import com.yundao.bp.iam.mapper.IamSessionMapper;
import com.yundao.bp.iam.mapper.IamUserMapper;
import com.yundao.bp.iam.mapper.IamUserRoleMapper;
import com.yundao.bp.iam.security.LoginUser;
import com.yundao.bp.iam.security.PasswordHasher;
import com.yundao.bp.iam.service.AuthService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 认证实现。
 */
@Service
public class AuthServiceImpl implements AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthServiceImpl.class);

    /** 令牌有效期（小时） */
    private static final int TOKEN_HOURS = 12;

    private final IamUserMapper userMapper;
    private final IamSessionMapper sessionMapper;
    private final IamUserRoleMapper userRoleMapper;
    private final IamRoleMapper roleMapper;
    private final IamRolePermissionMapper rolePermMapper;
    private final IamPermissionMapper permMapper;
    private final PasswordHasher hasher;
    private final SnowflakeIdGenerator idGen;

    public AuthServiceImpl(IamUserMapper userMapper, IamSessionMapper sessionMapper,
                           IamUserRoleMapper userRoleMapper, IamRoleMapper roleMapper,
                           IamRolePermissionMapper rolePermMapper,
                           IamPermissionMapper permMapper, PasswordHasher hasher,
                           SnowflakeIdGenerator idGen) {
        this.userMapper = userMapper;
        this.sessionMapper = sessionMapper;
        this.userRoleMapper = userRoleMapper;
        this.roleMapper = roleMapper;
        this.rolePermMapper = rolePermMapper;
        this.permMapper = permMapper;
        this.hasher = hasher;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public LoginVO login(LoginCmd cmd, String ip) {
        IamUser user = userMapper.selectOne(new LambdaQueryWrapper<IamUser>()
                .eq(IamUser::getUsername, cmd.username())
                .last("LIMIT 1"));
        // 统一话术：不区分"用户不存在"与"密码错误"，避免账号枚举
        if (user == null || !hasher.verify(cmd.password(), user.getPasswordHash())) {
            log.warn("登录失败：username={} ip={}", cmd.username(), ip);
            throw new BizException(ErrorCode.PARAM_INVALID, "登录名或密码错误");
        }
        if (!"ENABLED".equals(user.getStatus())) {
            throw BizException.stateConflict("账号已" + ("LOCKED".equals(user.getStatus())
                    ? "锁定" : "停用") + "，请联系管理员");
        }

        // 单设备登录：踢掉旧会话
        if (user.getSingleDevice() != null && user.getSingleDevice() == 1) {
            List<IamSession> olds = sessionMapper.selectList(
                    new LambdaQueryWrapper<IamSession>()
                            .eq(IamSession::getUserId, user.getId())
                            .eq(IamSession::getStatus, "ACTIVE"));
            for (IamSession s : olds) {
                s.setStatus("KICKED");
                sessionMapper.updateById(s);
            }
        }

        String token = hasher.newToken();
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime expire = now.plusHours(TOKEN_HOURS);

        IamSession s = new IamSession();
        s.setId(idGen.nextId());
        s.setTenantId(user.getTenantId());
        s.setUserId(user.getId());
        s.setTokenId(token);
        s.setDeviceType(cmd.deviceType() == null ? "WEB" : cmd.deviceType());
        s.setDeviceId(cmd.deviceId());
        s.setLoginIp(ip);
        s.setLoginTime(now);
        s.setExpireTime(expire);
        s.setStatus("ACTIVE");
        sessionMapper.insert(s);

        user.setLastLoginTime(now);
        user.setLastLoginIp(ip);
        user.setLoginCount((user.getLoginCount() == null ? 0 : user.getLoginCount()) + 1);
        user.setUpdateTime(now);
        userMapper.updateById(user);

        log.info("登录成功：{}（{}）ip={}", user.getUsername(), user.getRealName(), ip);
        return new LoginVO(token, user.getId(), user.getUsername(), user.getRealName(),
                user.getTenantId(), user.getOrgId(),
                user.getIsAdmin() != null && user.getIsAdmin() == 1, expire);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void logout(String token) {
        IamSession s = findByToken(token);
        if (s != null) {
            s.setStatus("LOGOUT");
            sessionMapper.updateById(s);
        }
    }

    @Override
    public MeVO me(Long userId) {
        IamUser user = userMapper.selectById(userId);
        if (user == null) {
            throw BizException.notFound("用户");
        }
        boolean admin = user.getIsAdmin() != null && user.getIsAdmin() == 1;
        List<Long> roleIds = roleIds(userId);
        Set<String> perms = admin ? Set.of("*") : permissionCodes(userId);
        return new MeVO(user.getId(), user.getUsername(), user.getRealName(),
                user.getTenantId(), user.getOrgId(), user.getUserType(), admin,
                new ArrayList<>(perms), roleIds);
    }

    @Override
    public LoginUser loadByToken(String token) {
        if (token == null || token.isBlank()) {
            return null;
        }
        IamSession s = findByToken(token);
        if (s == null || !"ACTIVE".equals(s.getStatus())) {
            return null;
        }
        if (s.getExpireTime() != null && s.getExpireTime().isBefore(LocalDateTime.now())) {
            s.setStatus("EXPIRED");
            sessionMapper.updateById(s);
            return null;
        }
        IamUser user = userMapper.selectById(s.getUserId());
        if (user == null || !"ENABLED".equals(user.getStatus())) {
            return null;
        }
        boolean admin = user.getIsAdmin() != null && user.getIsAdmin() == 1;
        Set<String> perms = admin ? Set.of("*") : permissionCodes(user.getId());
        return new LoginUser(user.getId(), user.getUsername(), user.getRealName(),
                user.getTenantId(), user.getOrgId(), admin, s.getTokenId(), perms);
    }

    @Override
    public Set<String> permissionCodes(Long userId) {
        List<Long> rids = roleIds(userId);
        if (rids.isEmpty()) {
            return Set.of();
        }
        List<IamRole> roles = roleMapper.selectBatchIds(rids);
        Set<Long> enabledRids = new HashSet<>();
        for (IamRole r : roles) {
            if ("ENABLED".equals(r.getStatus())) {
                enabledRids.add(r.getId());
            }
        }
        if (enabledRids.isEmpty()) {
            return Set.of();
        }
        List<IamRolePermission> rps = rolePermMapper.selectList(
                new LambdaQueryWrapper<IamRolePermission>()
                        .in(IamRolePermission::getRoleId, enabledRids));
        if (rps.isEmpty()) {
            return Set.of();
        }
        Set<Long> pids = new HashSet<>();
        rps.forEach(rp -> pids.add(rp.getPermissionId()));
        List<IamPermission> perms = permMapper.selectBatchIds(pids);
        Set<String> codes = new HashSet<>();
        for (IamPermission p : perms) {
            if ("ENABLED".equals(p.getStatus())) {
                codes.add(p.getPermCode());
            }
        }
        return codes;
    }

    private List<Long> roleIds(Long userId) {
        List<IamUserRole> urs = userRoleMapper.selectList(
                new LambdaQueryWrapper<IamUserRole>().eq(IamUserRole::getUserId, userId));
        List<Long> ids = new ArrayList<>();
        urs.forEach(u -> ids.add(u.getRoleId()));
        return ids;
    }

    private IamSession findByToken(String token) {
        if (token == null || token.isBlank()) {
            return null;
        }
        return sessionMapper.selectOne(new LambdaQueryWrapper<IamSession>()
                .eq(IamSession::getTokenId, token)
                .last("LIMIT 1"));
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
