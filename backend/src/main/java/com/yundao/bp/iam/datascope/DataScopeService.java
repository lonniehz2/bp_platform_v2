package com.yundao.bp.iam.datascope;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.entity.IamOrg;
import com.yundao.bp.iam.entity.IamRole;
import com.yundao.bp.iam.entity.IamUser;
import com.yundao.bp.iam.entity.IamUserRole;
import com.yundao.bp.iam.mapper.IamOrgMapper;
import com.yundao.bp.iam.mapper.IamRoleMapper;
import com.yundao.bp.iam.mapper.IamUserMapper;
import com.yundao.bp.iam.mapper.IamUserRoleMapper;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;

/**
 * 计算当前登录用户的数据范围。
 *
 * <p>多角色取最宽：ALL &gt; ORG_SUB &gt; ORG &gt; SELF。
 * 超管（isAdmin=1）直接 ALL，避免把自己锁在数据外。
 */
@Service
public class DataScopeService {

    private static final Map<String, Integer> RANK = Map.of(
            "SELF", 1, "ORG", 2, "ORG_SUB", 3, "ALL", 4);

    private final IamUserMapper userMapper;
    private final IamUserRoleMapper userRoleMapper;
    private final IamRoleMapper roleMapper;
    private final IamOrgMapper orgMapper;

    public DataScopeService(IamUserMapper userMapper, IamUserRoleMapper userRoleMapper,
                            IamRoleMapper roleMapper, IamOrgMapper orgMapper) {
        this.userMapper = userMapper;
        this.userRoleMapper = userRoleMapper;
        this.roleMapper = roleMapper;
        this.orgMapper = orgMapper;
    }

    /** 当前用户的数据范围；取不到用户时按最严（SELF）处理。 */
    public DataScope current() {
        Long userId = TenantContext.userId();
        if (userId == null) {
            return new DataScope("SELF", null, List.of(), null);
        }
        IamUser user = userMapper.selectById(userId);
        if (user == null) {
            return new DataScope("SELF", null, List.of(), null);
        }
        if (Integer.valueOf(1).equals(user.getIsAdmin())) {
            return new DataScope("ALL", user.getOrgId(), List.of(), user.getPersonId());
        }
        List<IamUserRole> links = userRoleMapper.selectList(
                new LambdaQueryWrapper<IamUserRole>().eq(IamUserRole::getUserId, userId));
        String widest = "SELF";
        if (!links.isEmpty()) {
            Set<Long> roleIds = new HashSet<>();
            for (IamUserRole l : links) {
                roleIds.add(l.getRoleId());
            }
            for (IamRole r : roleMapper.selectBatchIds(roleIds)) {
                String scope = normalize(r.getDataScope());
                if (RANK.getOrDefault(scope, 1) > RANK.getOrDefault(widest, 1)) {
                    widest = scope;
                }
            }
        }
        List<Long> orgIds = List.of();
        if ("ORG_SUB".equals(widest) && user.getOrgId() != null) {
            orgIds = subtree(user.getOrgId());
        }
        return new DataScope(widest, user.getOrgId(), orgIds, user.getPersonId());
    }

    /** 组织子树（按 parent_id 展开，含自身）。 */
    public List<Long> subtree(Long rootId) {
        List<IamOrg> all = orgMapper.selectList(new LambdaQueryWrapper<>());
        Map<Long, List<Long>> children = new HashMap<>();
        for (IamOrg o : all) {
            children.computeIfAbsent(o.getParentId(), k -> new ArrayList<>()).add(o.getId());
        }
        List<Long> out = new ArrayList<>();
        collect(rootId, children, out, new HashSet<>());
        return out;
    }

    private void collect(Long id, Map<Long, List<Long>> children, List<Long> out, Set<Long> seen) {
        if (id == null || !seen.add(id)) {
            return;
        }
        out.add(id);
        for (Long c : children.getOrDefault(id, List.of())) {
            collect(c, children, out, seen);
        }
    }

    /** 归一化历史别名：TENANT/OWN 视同 SELF；未知值按最严处理。 */
    private String normalize(String raw) {
        if (raw == null || raw.isBlank()) {
            return "SELF";
        }
        String v = raw.trim().toUpperCase();
        if ("TENANT".equals(v) || "OWN".equals(v) || "PERSON".equals(v)) {
            return "SELF";
        }
        if (RANK.containsKey(v)) {
            return v;
        }
        return "SELF";
    }
}
