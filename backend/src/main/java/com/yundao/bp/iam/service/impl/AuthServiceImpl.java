package com.yundao.bp.iam.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
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

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamTenantMapper tenantMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamOrgMapper orgMapper;

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
        // ⭐ 登录时还没有租户上下文，必须先建立，否则会话写入/登录信息更新会被租户拦截器拒绝
        String tenant = (cmd.tenantId() == null || cmd.tenantId().isBlank())
                ? "350600" : cmd.tenantId().trim();
        TenantContext.set(TenantInfo.of(tenant, null));

        IamUser user = userMapper.selectOne(new LambdaQueryWrapper<IamUser>()
                .eq(IamUser::getUsername, cmd.username())
                .last("LIMIT 1"));
        // 统一话术：不区分"用户不存在"与"密码错误"，避免账号枚举
        if (user == null || !hasher.verify(cmd.password(), user.getPasswordHash())) {
            log.warn("登录失败：username={} ip={}", cmd.username(), ip);
            throw new BizException(ErrorCode.PARAM_INVALID, "登录名或密码错误");
        }
        if (tenantMapper != null) {
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

        // 以用户真实租户为准（防止跨租户登录）
        TenantContext.set(TenantInfo.of(user.getTenantId(), user.getId()));

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
        String tenantName = null;
        if (tenantMapper != null && user.getTenantId() != null) {
            com.yundao.bp.iam.entity.IamTenant t = tenantMapper.selectOne(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                            <com.yundao.bp.iam.entity.IamTenant>()
                            .eq(com.yundao.bp.iam.entity.IamTenant::getTenantCode,
                                    user.getTenantId())
                            .last("LIMIT 1"));
            if (t != null) {
                tenantName = t.getTenantName();
            }
        }
        String orgName = null;
        if (user.getOrgId() == null) {
            orgName = "平台";
        } else if (orgMapper != null) {
            com.yundao.bp.iam.entity.IamOrg o = orgMapper.selectById(user.getOrgId());
            if (o != null) {
                orgName = o.getOrgName();
            }
        }
        return new MeVO(user.getId(), user.getUsername(), user.getRealName(),
                user.getTenantId(), user.getOrgId(), tenantName,
                orgName == null ? "平台" : orgName, user.getUserType(), admin,
                new ArrayList<>(perms), roleIds,
                user.getMustChangePassword() != null && user.getMustChangePassword() == 1);
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
        // ⭐ 以会话记录里的租户为准建立上下文（权威来源，非客户端传入）
        TenantContext.set(TenantInfo.of(s.getTenantId(), s.getUserId()));

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
        // 绕过租户过滤：认证时尚无租户上下文，且令牌全局唯一
        return sessionMapper.selectByTokenIgnoreTenant(token);
    }

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
}
