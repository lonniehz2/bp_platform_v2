package com.yundao.bp.iam.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.entity.IamPermission;
import com.yundao.bp.iam.entity.IamRole;
import com.yundao.bp.iam.entity.IamRolePermission;
import com.yundao.bp.iam.entity.IamUser;
import com.yundao.bp.iam.entity.IamUserRole;
import com.yundao.bp.iam.mapper.IamPermissionMapper;
import com.yundao.bp.iam.mapper.IamRoleMapper;
import com.yundao.bp.iam.mapper.IamRolePermissionMapper;
import com.yundao.bp.iam.mapper.IamUserMapper;
import com.yundao.bp.iam.mapper.IamUserRoleMapper;
import com.yundao.bp.iam.security.PasswordHasher;
import com.yundao.bp.iam.security.RequirePerm;
import java.time.LocalDateTime;
import java.util.Set;
import java.util.Map;
import java.util.HashSet;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.List;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 用户 / 角色 / 权限管理接口。
 *
 * <p>全部标注 {@link RequirePerm}，仅具备对应权限的账号可操作。
 */
@RestController
@RequestMapping("/api/v1/rbac")
public class RbacController {

    private final IamUserMapper userMapper;
    private final IamRoleMapper roleMapper;
    private final IamPermissionMapper permMapper;
    private final IamUserRoleMapper userRoleMapper;
    private final IamRolePermissionMapper rolePermMapper;
    private final PasswordHasher hasher;
    private final SnowflakeIdGenerator idGen;

    public RbacController(IamUserMapper userMapper, IamRoleMapper roleMapper,
                          IamPermissionMapper permMapper, IamUserRoleMapper userRoleMapper,
                          IamRolePermissionMapper rolePermMapper, PasswordHasher hasher,
                          SnowflakeIdGenerator idGen) {
        this.userMapper = userMapper;
        this.roleMapper = roleMapper;
        this.permMapper = permMapper;
        this.userRoleMapper = userRoleMapper;
        this.rolePermMapper = rolePermMapper;
        this.hasher = hasher;
        this.idGen = idGen;
    }

    // ---------- 用户 ----------

    @PostMapping("/users")
    @RequirePerm("iam:user:create")
    @Transactional(rollbackFor = Exception.class)
    public R<IamUser> createUser(@RequestBody UserCmd cmd) {
        if (cmd.username() == null || cmd.username().isBlank()) {
            throw BizException.paramInvalid("登录名不能为空");
        }
        Long dup = userMapper.selectCount(new LambdaQueryWrapper<IamUser>()
                .eq(IamUser::getUsername, cmd.username()));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "登录名已存在");
        }
        long id = idGen.nextId();
        IamUser u = new IamUser();
        u.setId(id);
        u.setTenantId(TenantContext.tenantId());
        u.setUsername(cmd.username());
        u.setPasswordHash(hasher.hash(cmd.password() == null ? "123456" : cmd.password()));
        u.setRealName(cmd.realName());
        u.setOrgId(cmd.orgId());
        u.setUserType("STAFF");  // 历史字段，系统概念上不再使用用户类型
        u.setIsAdmin(0);
        u.setSingleDevice(0);
        u.setLoginCount(0);
        u.setStatus("ENABLED");
        u.setIsDeleted(0);
        u.setCreateTime(LocalDateTime.now());
        u.setUpdateTime(LocalDateTime.now());
        userMapper.insert(u);
        // 直接按所选角色绑定（系统不再有「用户类型」概念）；
        // 未选角色时兜底绑定 STAFF 默认角色，保证新账号不是空权限
        java.util.List<Long> roleIds = cmd.roleIds();
        if (roleIds == null || roleIds.isEmpty()) {
            IamRole def = roleMapper.selectOne(new LambdaQueryWrapper<IamRole>()
                    .eq(IamRole::getRoleCode, "STAFF").last("limit 1"));
            roleIds = def == null ? java.util.List.of() : java.util.List.of(def.getId());
        }
        for (Long rid : roleIds) {
            IamUserRole link = new IamUserRole();
            link.setId(idGen.nextId());
            link.setTenantId(TenantContext.tenantId());
            link.setUserId(id);
            link.setRoleId(rid);
            link.setCreateTime(LocalDateTime.now());
            userRoleMapper.insert(link);
        }
        u.setPasswordHash(null);
        return R.ok(u);
    }

    @GetMapping("/users")
    @RequirePerm("iam:user:list")
    public R<List<IamUser>> listUsers(@RequestParam(required = false) String keyword) {
        LambdaQueryWrapper<IamUser> qw = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isBlank()) {
            String k = keyword.trim();
            qw.and(w -> w.like(IamUser::getUsername, k).or().like(IamUser::getRealName, k));
        }
        List<IamUser> list = userMapper.selectList(qw);
        list.forEach(u -> u.setPasswordHash(null));
        fillRoleNames(list);
        return R.ok(list);
    }


    /** 批量补用户角色名（一次查关联表 + 角色表，避免逐条查询） */
    private void fillRoleNames(List<IamUser> users) {
        if (users == null || users.isEmpty()) {
            return;
        }
        List<Long> ids = new ArrayList<>();
        for (IamUser u : users) {
            ids.add(u.getId());
        }
        List<IamUserRole> links = userRoleMapper.selectList(
                new LambdaQueryWrapper<IamUserRole>()
                        .in(IamUserRole::getUserId, ids));
        if (links.isEmpty()) {
            return;
        }
        Set<Long> roleIds = new HashSet<>();
        for (IamUserRole l : links) {
            roleIds.add(l.getRoleId());
        }
        Map<Long, String> nameById = new HashMap<>();
        for (IamRole r : roleMapper.selectBatchIds(roleIds)) {
            nameById.put(r.getId(), r.getRoleName());
        }
        Map<Long, List<String>> byUser = new HashMap<>();
        for (IamUserRole l : links) {
            String nm = nameById.get(l.getRoleId());
            if (nm != null) {
                byUser.computeIfAbsent(l.getUserId(), k -> new ArrayList<>()).add(nm);
            }
        }
        for (IamUser u : users) {
            List<String> names = byUser.get(u.getId());
            u.setRoleNames(names == null ? "" : String.join("、", names));
        }
    }

    /** 某用户的角色列表（用户页回显用）。 */
    @GetMapping("/users/{userId}/roles")
    @RequirePerm("iam:user:list")
    public R<List<IamRole>> userRoles(@PathVariable Long userId) {
        List<IamUserRole> links = userRoleMapper.selectList(
                new LambdaQueryWrapper<IamUserRole>().eq(IamUserRole::getUserId, userId));
        if (links.isEmpty()) {
            return R.ok(List.of());
        }
        List<Long> ids = new ArrayList<>();
        for (IamUserRole l : links) {
            ids.add(l.getRoleId());
        }
        return R.ok(roleMapper.selectBatchIds(ids));
    }

    /** 给用户分配角色。 */
    @PostMapping("/users/{userId}/roles")
    @RequirePerm("iam:user:assign")
    @Transactional(rollbackFor = Exception.class)
    public R<Integer> assignRoles(@PathVariable Long userId, @RequestBody IdsCmd cmd) {
        userRoleMapper.delete(new LambdaQueryWrapper<IamUserRole>()
                .eq(IamUserRole::getUserId, userId));
        int n = 0;
        for (Long rid : cmd.ids()) {
            IamUserRole ur = new IamUserRole();
            ur.setId(idGen.nextId());
            ur.setTenantId(TenantContext.tenantId());
            ur.setUserId(userId);
            ur.setRoleId(rid);
            ur.setCreateTime(LocalDateTime.now());
            userRoleMapper.insert(ur);
            n++;
        }
        return R.ok(n);
    }

    // ---------- 角色 ----------

    @PostMapping("/roles")
    @RequirePerm("iam:role:create")
    @Transactional(rollbackFor = Exception.class)
    public R<IamRole> createRole(@RequestBody RoleCmd cmd) {
        Long dup = roleMapper.selectCount(new LambdaQueryWrapper<IamRole>()
                .eq(IamRole::getRoleCode, cmd.roleCode()));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "角色编码已存在");
        }
        long id = idGen.nextId();
        IamRole r = new IamRole();
        r.setId(id);
        r.setTenantId(TenantContext.tenantId());
        r.setRoleCode(cmd.roleCode());
        r.setRoleName(cmd.roleName());
        r.setRoleType("CUSTOM");
        r.setDataScope(cmd.dataScope() == null ? "ORG" : cmd.dataScope());
        r.setSortNo(0);
        r.setStatus("ENABLED");
        r.setIsDeleted(0);
        r.setCreateTime(LocalDateTime.now());
        r.setUpdateTime(LocalDateTime.now());
        roleMapper.insert(r);
        return R.ok(r);
    }

    /** 更新角色基本信息与数据范围（角色配置页同一处保存）。 */
    @PutMapping("/roles/{roleId}")
    @RequirePerm("iam:role:list")
    @Transactional(rollbackFor = Exception.class)
    public R<IamRole> updateRole(@PathVariable Long roleId, @RequestBody RoleUpdateCmd cmd) {
        IamRole r = roleMapper.selectById(roleId);
        if (r == null) {
            throw BizException.notFound("角色");
        }
        if (cmd.roleName() != null && !cmd.roleName().isBlank()) {
            r.setRoleName(cmd.roleName().trim());
        }
        if (cmd.dataScope() != null && !cmd.dataScope().isBlank()) {
            r.setDataScope(cmd.dataScope());
        }
        if (cmd.status() != null && !cmd.status().isBlank()) {
            r.setStatus(cmd.status());
        }
        r.setUpdateTime(LocalDateTime.now());
        roleMapper.updateById(r);
        return R.ok(r);
    }

    @GetMapping("/roles")
    @RequirePerm("iam:role:list")
    public R<List<IamRole>> listRoles(@RequestParam(required = false) String keyword) {
        LambdaQueryWrapper<IamRole> qw = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isBlank()) {
            String k = keyword.trim();
            qw.and(w -> w.like(IamRole::getRoleCode, k).or().like(IamRole::getRoleName, k));
        }
        return R.ok(roleMapper.selectList(qw));
    }

    /** 给角色分配权限。 */
    @PostMapping("/roles/{roleId}/permissions")
    @RequirePerm("iam:role:assign")
    @Transactional(rollbackFor = Exception.class)
    public R<Integer> assignPermissions(@PathVariable Long roleId, @RequestBody IdsCmd cmd) {
        rolePermMapper.delete(new LambdaQueryWrapper<IamRolePermission>()
                .eq(IamRolePermission::getRoleId, roleId));
        int n = 0;
        for (Long pid : cmd.ids()) {
            IamRolePermission rp = new IamRolePermission();
            rp.setId(idGen.nextId());
            rp.setTenantId(TenantContext.tenantId());
            rp.setRoleId(roleId);
            rp.setPermissionId(pid);
            rp.setCreateTime(LocalDateTime.now());
            rolePermMapper.insert(rp);
            n++;
        }
        return R.ok(n);
    }

    /** 该角色已授予的权限列表（角色配置页回显用）。 */
    @GetMapping("/roles/{roleId}/permissions")
    @RequirePerm("iam:role:list")
    public R<java.util.List<IamPermission>> rolePermissions(@PathVariable Long roleId) {
        java.util.List<IamRolePermission> links = rolePermMapper.selectList(
                new LambdaQueryWrapper<IamRolePermission>()
                        .eq(IamRolePermission::getRoleId, roleId));
        java.util.List<Long> ids = new java.util.ArrayList<>();
        for (IamRolePermission rp : links) {
            ids.add(rp.getPermissionId());
        }
        if (ids.isEmpty()) {
            return R.ok(java.util.List.of());
        }
        return R.ok(permMapper.selectBatchIds(ids));
    }

    // ---------- 权限 ----------

    @PostMapping("/permissions")
    @RequirePerm("iam:perm:create")
    @Transactional(rollbackFor = Exception.class)
    public R<IamPermission> createPermission(@RequestBody PermCmd cmd) {
        Long dup = permMapper.selectCount(new LambdaQueryWrapper<IamPermission>()
                .eq(IamPermission::getPermCode, cmd.permCode()));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "权限标识已存在");
        }
        long id = idGen.nextId();
        IamPermission p = new IamPermission();
        p.setId(id);
        p.setParentId(cmd.parentId());
        p.setPermCode(cmd.permCode());
        p.setPermName(cmd.permName());
        p.setPermType(cmd.permType() == null ? "API" : cmd.permType());
        p.setRoutePath(cmd.routePath());
        p.setScenario(cmd.scenario());
        p.setSortNo(cmd.sortNo() == null ? 0 : cmd.sortNo());
        p.setStatus("ENABLED");
        p.setCreateTime(LocalDateTime.now());
        permMapper.insert(p);
        return R.ok(p);
    }

    @com.yundao.bp.iam.security.RequirePerm("rbac:perm:view")
    @GetMapping("/permissions")
    public R<List<IamPermission>> listPermissions(@RequestParam(required = false) String keyword) {
        LambdaQueryWrapper<IamPermission> qw = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isBlank()) {
            String k = keyword.trim();
            qw.and(w -> w.like(IamPermission::getPermCode, k)
                    .or().like(IamPermission::getPermName, k));
        }
        qw.orderByAsc(IamPermission::getSortNo);
        return R.ok(permMapper.selectList(qw));
    }

    // ---------- 请求体 ----------

    public record UserCmd(String username, String password, String realName, Long orgId,
                          java.util.List<Long> roleIds) {
    }

    public record RoleUpdateCmd(String roleName, String dataScope, String status) {
    }

    public record RoleCmd(String roleCode, String roleName, String dataScope) {
    }

    public record PermCmd(Long parentId, String permCode, String permName, String permType,
                          String routePath, String scenario, Integer sortNo) {
    }

    public record IdsCmd(List<Long> ids) {
    }
}
