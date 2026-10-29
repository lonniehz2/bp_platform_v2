package com.yundao.bp.iam.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.iam.dto.*;
import com.yundao.bp.iam.entity.*;
import com.yundao.bp.iam.mapper.*;
import com.yundao.bp.iam.security.PasswordHasher;
import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 平台生命周期与平台管理员账号管理（运营超管使用）。 */
@Service
public class PlatformManageService {

    private static final Logger log = LoggerFactory.getLogger(PlatformManageService.class);
    private static final SecureRandom RANDOM = new SecureRandom();
    private static final String PWD_CHARS =
            "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%";

    private final IamTenantMapper tenantMapper;
    private final IamOrgMapper orgMapper;
    private final IamUserMapper userMapper;
    private final IamUserRoleMapper userRoleMapper;
    private final IamRoleMapper roleMapper;
    private final IamSessionMapper sessionMapper;
    private final PlatformAuditMapper auditMapper;
    private final TenantBrandingMapper brandingMapper;
    private final PasswordHasher hasher;
    private final SnowflakeIdGenerator idGen;
    private final JdbcTemplate jdbc;

    public PlatformManageService(IamTenantMapper tenantMapper, IamOrgMapper orgMapper,
                                 IamUserMapper userMapper, IamUserRoleMapper userRoleMapper,
                                 IamRoleMapper roleMapper, IamSessionMapper sessionMapper,
                                 PlatformAuditMapper auditMapper,
                                 TenantBrandingMapper brandingMapper,
                                 PasswordHasher hasher, SnowflakeIdGenerator idGen,
                                 JdbcTemplate jdbc) {
        this.tenantMapper = tenantMapper;
        this.orgMapper = orgMapper;
        this.userMapper = userMapper;
        this.userRoleMapper = userRoleMapper;
        this.roleMapper = roleMapper;
        this.sessionMapper = sessionMapper;
        this.auditMapper = auditMapper;
        this.brandingMapper = brandingMapper;
        this.hasher = hasher;
        this.idGen = idGen;
        this.jdbc = jdbc;
    }

    public List<PlatformVO> list(String keyword, String status) {
        List<IamTenant> list = tenantMapper.selectList(new LambdaQueryWrapper<IamTenant>()
                .eq(IamTenant::getDeleted, 0)
                .eq(status != null && !status.isBlank(), IamTenant::getStatus, status)
                .and(keyword != null && !keyword.isBlank(), w -> w
                        .like(IamTenant::getTenantName, keyword)
                        .or().like(IamTenant::getTenantCode, keyword))
                .orderByAsc(IamTenant::getTenantCode));
        List<PlatformVO> out = new ArrayList<>();
        for (IamTenant t : list) {
            TenantContext.set(TenantInfo.of(t.getTenantCode(), null));
            out.add(vo(t));
        }
        return out;
    }

    public PlatformVO detail(Long id) {
        IamTenant t = require(id);
        TenantContext.set(TenantInfo.of(t.getTenantCode(), null));
        return vo(t);
    }

    @Transactional(rollbackFor = Exception.class)
    public PlatformCreateResult create(PlatformCreateCmd cmd, PlatformOperator op, String ip) {
        String region = cmd.regionCode().trim();
        if (!region.matches("\\d{6}")) {
            throw new BizException(ErrorCode.PARAM_INVALID, "行政区划应为 6 位数字编码");
        }
        String code = nextCode(region);
        String type = cmd.tenantType() == null || cmd.tenantType().isBlank()
                ? "GOV" : cmd.tenantType();
        LocalDateTime now = LocalDateTime.now();
        long tenantId = idGen.nextId();
        IamTenant t = new IamTenant();
        t.setId(tenantId);
        t.setTenantCode(code);
        t.setTenantName(cmd.tenantName().trim());
        t.setTenantType(type);
        t.setRegionCode(region);
        t.setIsolationMode("ROW");
        t.setStatus("ENABLED");
        t.setContactName(cmd.contactName());
        t.setContactPhone(cmd.contactPhone());
        t.setBusinessTypeCode("BAOZHANG");
        t.setDeleted(0);
        t.setCreateBy(op.getUsername());
        t.setCreateTime(now);
        t.setUpdateTime(now);
        tenantMapper.insert(t);
        TenantContext.set(TenantInfo.of(code, null));

        IamOrg org = new IamOrg();
        org.setId(idGen.nextId());
        org.setTenantId(code);
        org.setOrgCode("PLATFORM");
        org.setOrgName("平台");
        org.setParentId(null);
        org.setOrgPath("/");
        org.setOrgLevel(1);
        org.setOrgType("COMPANY");
        org.setSortNo(0);
        org.setStatus("ENABLED");
        org.setIsDeleted(0);
        org.setCreateTime(now);
        org.setUpdateTime(now);
        orgMapper.insert(org);

        String pwd = randomPassword();
        createAdminUser(code, org.getId(), cmd.adminUsername().trim(),
                cmd.adminRealName(), null, null, pwd, now);
        audit(op, code, "CREATE_PLATFORM", "新建平台 " + t.getTenantName() + "（编码 " + code + "）", ip);
        log.info("平台创建：{} {} by {}", code, t.getTenantName(), op.getUsername());
        return new PlatformCreateResult(vo(t), cmd.adminUsername(), pwd);
    }

    @Transactional(rollbackFor = Exception.class)
    public PlatformVO update(Long id, PlatformUpdateCmd cmd, PlatformOperator op, String ip) {
        IamTenant t = require(id);
        t.setTenantName(cmd.tenantName().trim());
        if (cmd.tenantType() != null && !cmd.tenantType().isBlank()) {
            t.setTenantType(cmd.tenantType());
        }
        if (cmd.regionCode() != null && !cmd.regionCode().isBlank()) {
            if (!cmd.regionCode().matches("\\d{6}")) {
                throw new BizException(ErrorCode.PARAM_INVALID, "行政区划应为 6 位数字编码");
            }
            t.setRegionCode(cmd.regionCode());
        }
        t.setContactName(cmd.contactName());
        t.setContactPhone(cmd.contactPhone());
        t.setUpdateTime(LocalDateTime.now());
        tenantMapper.updateById(t);
        audit(op, t.getTenantCode(), "UPDATE_PLATFORM", "修改平台信息", ip);
        return vo(t);
    }

    @Transactional(rollbackFor = Exception.class)
    public void setStatus(Long id, String status, PlatformOperator op, String ip) {
        IamTenant t = require(id);
        if ("ENABLED".equals(status) && "ARCHIVED".equals(t.getStatus())) {
            throw new BizException(ErrorCode.STATE_CONFLICT, "已归档平台请先恢复");
        }
        t.setStatus(status);
        t.setUpdateTime(LocalDateTime.now());
        tenantMapper.updateById(t);
        if ("DISABLED".equals(status)) {
            jdbc.update("update bp_iam_session set status='KICKED' where tenant_id=? and status='ACTIVE'",
                    t.getTenantCode());
        }
        audit(op, t.getTenantCode(), "ENABLED".equals(status) ? "ENABLE_PLATFORM" : "DISABLE_PLATFORM",
                "平台状态改为 " + status, ip);
    }

    @Transactional(rollbackFor = Exception.class)
    public void archive(Long id, PlatformOperator op, String ip) {
        IamTenant t = require(id);
        if (!"DISABLED".equals(t.getStatus())) {
            throw new BizException(ErrorCode.STATE_CONFLICT, "仅停用状态的平台可归档");
        }
        t.setStatus("ARCHIVED");
        t.setDeleted(1);
        t.setArchiveTime(LocalDateTime.now());
        t.setUpdateTime(LocalDateTime.now());
        tenantMapper.updateById(t);
        jdbc.update("update bp_iam_session set status='KICKED' where tenant_id=? and status='ACTIVE'",
                t.getTenantCode());
        audit(op, t.getTenantCode(), "ARCHIVE_PLATFORM", "归档平台", ip);
    }

    @Transactional(rollbackFor = Exception.class)
    public void restore(Long id, PlatformOperator op, String ip) {
        IamTenant t = require(id);
        t.setStatus("DISABLED");
        t.setDeleted(0);
        t.setArchiveTime(null);
        t.setUpdateTime(LocalDateTime.now());
        tenantMapper.updateById(t);
        audit(op, t.getTenantCode(), "RESTORE_PLATFORM", "恢复归档平台", ip);
    }

    public List<PlatformAdminVO> admins(Long id) {
        IamTenant t = require(id);
        TenantContext.set(TenantInfo.of(t.getTenantCode(), null));
        List<IamUser> users = userMapper.selectList(new LambdaQueryWrapper<IamUser>()
                .eq(IamUser::getTenantId, t.getTenantCode())
                .eq(IamUser::getIsAdmin, 1)
                .eq(IamUser::getIsDeleted, 0)
                .orderByAsc(IamUser::getCreateTime));
        List<PlatformAdminVO> out = new ArrayList<>();
        for (IamUser u : users) {
            out.add(adminVO(u));
        }
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public PlatformAdminResetVO createAdmin(Long id, PlatformAdminCreateCmd cmd,
                                            PlatformOperator op, String ip) {
        IamTenant t = require(id);
        TenantContext.set(TenantInfo.of(t.getTenantCode(), null));
        if ("ARCHIVED".equals(t.getStatus())) {
            throw new BizException(ErrorCode.STATE_CONFLICT, "已归档平台不能新增管理员");
        }
        Long exists = userMapper.selectCount(new LambdaQueryWrapper<IamUser>()
                .eq(IamUser::getTenantId, t.getTenantCode())
                .eq(IamUser::getUsername, cmd.username())
                .eq(IamUser::getIsDeleted, 0));
        if (exists != null && exists > 0) {
            throw new BizException(ErrorCode.STATE_CONFLICT, "该平台下账号已存在");
        }
        IamOrg org = orgMapper.selectOne(new LambdaQueryWrapper<IamOrg>()
                .eq(IamOrg::getTenantId, t.getTenantCode())
                .eq(IamOrg::getOrgCode, "PLATFORM")
                .last("LIMIT 1"));
        String pwd = randomPassword();
        LocalDateTime now = LocalDateTime.now();
        IamUser u = createAdminUser(t.getTenantCode(), org == null ? null : org.getId(),
                cmd.username(), cmd.realName(), cmd.phone(), cmd.email(), pwd, now);
        audit(op, t.getTenantCode(), "CREATE_ADMIN", "新增平台管理员 " + u.getUsername(), ip);
        return new PlatformAdminResetVO(u.getId(), u.getUsername(), pwd, true);
    }

    @Transactional(rollbackFor = Exception.class)
    public PlatformAdminResetVO resetPassword(Long platformId, Long userId,
                                              PlatformOperator op, String ip) {
        IamUser u = requireAdmin(platformId, userId);
        String pwd = randomPassword();
        u.setPasswordHash(hasher.hash(pwd));
        u.setMustChangePassword(1);
        u.setFailCount(0);
        u.setLockedUntil(null);
        u.setPwdUpdateTime(LocalDateTime.now());
        u.setUpdateTime(LocalDateTime.now());
        userMapper.updateById(u);
        audit(op, u.getTenantId(), "RESET_ADMIN_PWD", "重置管理员密码 " + u.getUsername(), ip);
        return new PlatformAdminResetVO(u.getId(), u.getUsername(), pwd, true);
    }

    @Transactional(rollbackFor = Exception.class)
    public void setAdminStatus(Long platformId, Long userId, String status,
                               PlatformOperator op, String ip) {
        IamUser u = requireAdmin(platformId, userId);
        if ("DISABLED".equals(status)) {
            Long active = userMapper.selectCount(new LambdaQueryWrapper<IamUser>()
                    .eq(IamUser::getTenantId, u.getTenantId())
                    .eq(IamUser::getIsAdmin, 1)
                    .eq(IamUser::getStatus, "ENABLED")
                    .eq(IamUser::getIsDeleted, 0)
                    .ne(IamUser::getId, u.getId()));
            if (active == null || active == 0) {
                throw new BizException(ErrorCode.STATE_CONFLICT, "至少保留一个启用的平台管理员");
            }
        }
        u.setStatus(status);
        u.setUpdateTime(LocalDateTime.now());
        userMapper.updateById(u);
        audit(op, u.getTenantId(), "ENABLED".equals(status) ? "ENABLE_ADMIN" : "DISABLE_ADMIN",
                "管理员状态改为 " + status + "：" + u.getUsername(), ip);
    }

    @Transactional(rollbackFor = Exception.class)
    public void unlockAdmin(Long platformId, Long userId, PlatformOperator op, String ip) {
        IamUser u = requireAdmin(platformId, userId);
        u.setFailCount(0);
        u.setLockedUntil(null);
        if ("LOCKED".equals(u.getStatus())) {
            u.setStatus("ENABLED");
        }
        u.setUpdateTime(LocalDateTime.now());
        userMapper.updateById(u);
        audit(op, u.getTenantId(), "UNLOCK_ADMIN", "解锁管理员 " + u.getUsername(), ip);
    }

    public PageResult<PlatformAuditVO> audits(long pageNum, long pageSize) {
        Page<PlatformAudit> page = auditMapper.selectPage(new Page<>(pageNum, pageSize),
                new LambdaQueryWrapper<PlatformAudit>()
                        .orderByDesc(PlatformAudit::getCreateTime));
        List<PlatformAuditVO> rows = new ArrayList<>();
        for (PlatformAudit a : page.getRecords()) {
            rows.add(new PlatformAuditVO(a.getId(), a.getOperatorName(), a.getPlatformCode(),
                    a.getAction(), a.getDetail(), a.getIp(), a.getCreateTime()));
        }
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    // ---------------- 内部 ----------------

    private IamUser createAdminUser(String tenantCode, Long orgId, String username,
                                    String realName, String phone, String email,
                                    String rawPwd, LocalDateTime now) {
        IamUser u = new IamUser();
        u.setId(idGen.nextId());
        u.setTenantId(tenantCode);
        u.setUsername(username);
        u.setRealName(realName == null || realName.isBlank() ? username : realName);
        u.setPhone(phone);
        u.setEmail(email);
        u.setOrgId(orgId);
        u.setUserType("STAFF");
        u.setIsAdmin(1);
        u.setSingleDevice(0);
        u.setStatus("ENABLED");
        u.setPasswordHash(hasher.hash(rawPwd));
        u.setPwdUpdateTime(now);
        u.setMustChangePassword(1);
        u.setFailCount(0);
        u.setIsDeleted(0);
        u.setCreateBy("platform-operator");
        u.setCreateTime(now);
        u.setUpdateTime(now);
        userMapper.insert(u);
        // 若该平台已有默认角色 STAFF，则绑定，便于后续按角色授权
        IamRole role = roleMapper.selectOne(new LambdaQueryWrapper<IamRole>()
                .eq(IamRole::getTenantId, tenantCode)
                .eq(IamRole::getRoleCode, "STAFF")
                .last("LIMIT 1"));
        if (role != null) {
            IamUserRole ur = new IamUserRole();
            ur.setId(idGen.nextId());
            ur.setTenantId(tenantCode);
            ur.setUserId(u.getId());
            ur.setRoleId(role.getId());
            ur.setOrgId(orgId);
            ur.setCreateBy("platform-operator");
            ur.setCreateTime(now);
            userRoleMapper.insert(ur);
        }
        return u;
    }

    private String nextCode(String region) {
        jdbc.update("insert into bp_sys_platform_seq(region_code, seq) values(?, 1) "
                + "on duplicate key update seq = seq + 1", region);
        Integer seq = jdbc.queryForObject(
                "select seq from bp_sys_platform_seq where region_code=?", Integer.class, region);
        String code = region + String.format("%03d", seq == null ? 1 : seq);
        Long exists = tenantMapper.selectCount(new LambdaQueryWrapper<IamTenant>()
                .eq(IamTenant::getTenantCode, code));
        if (exists != null && exists > 0) {
            // 极端并发冲突：再取一个
            return nextCode(region);
        }
        return code;
    }

    private static String randomPassword() {
        StringBuilder sb = new StringBuilder("Bp");
        for (int i = 0; i < 10; i++) {
            sb.append(PWD_CHARS.charAt(RANDOM.nextInt(PWD_CHARS.length())));
        }
        return sb.toString();
    }

    private IamTenant require(Long id) {
        IamTenant t = tenantMapper.selectById(id);
        if (t == null) {
            throw new BizException(ErrorCode.NOT_FOUND, "平台不存在");
        }
        return t;
    }

    private IamUser requireAdmin(Long platformId, Long userId) {
        IamTenant t = require(platformId);
        TenantContext.set(TenantInfo.of(t.getTenantCode(), null));
        IamUser u = userMapper.selectById(userId);
        if (u == null || !t.getTenantCode().equals(u.getTenantId())
                || u.getIsAdmin() == null || u.getIsAdmin() != 1) {
            throw new BizException(ErrorCode.NOT_FOUND, "平台管理员不存在");
        }
        return u;
    }

    private PlatformVO vo(IamTenant t) {
        Long count = userMapper.selectCount(new LambdaQueryWrapper<IamUser>()
                .eq(IamUser::getTenantId, t.getTenantCode())
                .eq(IamUser::getIsAdmin, 1)
                .eq(IamUser::getIsDeleted, 0));
        return new PlatformVO(t.getId(), t.getTenantCode(), t.getTenantName(),
                t.getTenantType(), t.getRegionCode(), t.getStatus(), t.getContactName(),
                t.getContactPhone(), t.getBusinessTypeCode(), count,
                t.getCreateTime(), t.getArchiveTime());
    }

    private PlatformAdminVO adminVO(IamUser u) {
        return new PlatformAdminVO(u.getId(), u.getUsername(), u.getRealName(), u.getPhone(),
                u.getStatus(),
                u.getMustChangePassword() != null && u.getMustChangePassword() == 1,
                u.getLastLoginTime(), u.getLockedUntil());
    }

    private void audit(PlatformOperator op, String code, String action, String detail, String ip) {
        PlatformAudit a = new PlatformAudit();
        a.setId(idGen.nextId());
        a.setOperatorId(op.getId());
        a.setOperatorName(op.getRealName() == null ? op.getUsername() : op.getRealName());
        a.setPlatformCode(code);
        a.setAction(action);
        a.setDetail(detail);
        a.setIp(ip);
        a.setCreateTime(LocalDateTime.now());
        auditMapper.insert(a);
    }
}
