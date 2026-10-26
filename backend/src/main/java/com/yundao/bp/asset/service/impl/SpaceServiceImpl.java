package com.yundao.bp.asset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.constant.SpaceType;
import com.yundao.bp.asset.dto.SpaceCreateCmd;
import com.yundao.bp.asset.dto.SpaceVO;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.entity.AssetSpace;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.mapper.AssetSpaceMapper;
import com.yundao.bp.asset.service.SpaceService;
import com.yundao.bp.asset.util.PathCodeUtil;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 空间树服务实现。
 *
 * <p>关键规则（{@code 03_数据库设计说明.md} §3.2.0）：
 * <ol>
 *   <li>层级链 {@code 楼栋→单元→楼层→房间→床位}，父子类型必须合法</li>
 *   <li>{@code path_code} 每级 2 位、结尾带 {@code /}（防前缀误匹配）</li>
 *   <li>{@code space_path} 存祖先 ID 链，供子树查询与权限继承</li>
 *   <li>删除前校验：有子节点或有房源则拒绝</li>
 * </ol>
 */
@Service
public class SpaceServiceImpl implements SpaceService {

    private final AssetSpaceMapper spaceMapper;
    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;

    public SpaceServiceImpl(AssetSpaceMapper spaceMapper,
                            AssetHouseMapper houseMapper,
                            SnowflakeIdGenerator idGen) {
        this.spaceMapper = spaceMapper;
        this.houseMapper = houseMapper;
        this.idGen = idGen;
    }

    /**
     * 同组织、同父节点下的下一个可用序号。
     *
     * <p>用于在未显式指定 {@code sortNo} 时自动递增，保证同级 {@code path_code} 唯一。
     *
     * <p>⚠️ 并发下极端情况可能撞号（两个请求同时读到同一最大值）。
     * 当前库上 {@code path_code} 只有普通索引 {@code idx_tenant_pathcode}，
     * <b>没有唯一约束兜底</b>；建议后续补
     * {@code uk_tenant_org_path(tenant_id, org_id, path_code, is_deleted)}。
     */
    private int nextSortNo(Long orgId, Long parentId) {
        List<AssetSpace> siblings = spaceMapper.selectList(new LambdaQueryWrapper<AssetSpace>()
                .eq(AssetSpace::getOrgId, orgId)
                .eq(parentId != null, AssetSpace::getParentId, parentId)
                .isNull(parentId == null, AssetSpace::getParentId));
        int max = 0;
        for (AssetSpace s : siblings) {
            if (s.getSortNo() != null && s.getSortNo() > max) {
                max = s.getSortNo();
            }
        }
        return max + 1;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SpaceVO create(SpaceCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        SpaceType type = parseType(cmd.spaceType());

        // 编码唯一（插件自动限定租户）
        Long dup = spaceMapper.selectCount(new LambdaQueryWrapper<AssetSpace>()
                .eq(AssetSpace::getSpaceCode, cmd.spaceCode()));
        if (dup != null && dup > 0) {
            throw new BizException(ErrorCode.DUPLICATED, "空间编码已存在: " + cmd.spaceCode());
        }

        AssetSpace parent = null;
        if (cmd.parentId() != null) {
            parent = spaceMapper.selectById(cmd.parentId());
            if (parent == null) {
                throw BizException.notFound("父空间节点");
            }
            // ★ 父子类型校验：禁止乱挂（如把房间挂到楼栋下）
            SpaceType parentType = parseType(parent.getSpaceType());
            SpaceType expected = SpaceType.nextOf(parentType);
            if (expected == null) {
                throw BizException.stateConflict(
                        parentType.label() + " 下不允许再建子节点");
            }
            // 套内隔间：允许「房间下再建房间」（一套房分隔成多个独立房间出租），
            // 此时内部门锁挂子房间、入户门锁挂外层房间，授权按祖先链继承。
            boolean innerRoom = parentType == SpaceType.ROOM && type == SpaceType.ROOM;
            if (expected != type && !innerRoom) {
                throw BizException.stateConflict(
                        parentType.label() + " 下只能是 " + expected.label()
                                + (parentType == SpaceType.ROOM ? " 或套内房间" : "")
                                + "，实际为 " + type.label());
            }
        } else if (type != SpaceType.BUILDING && type != SpaceType.AREA) {
            // 无父节点时只允许作为顶层（楼栋/片区），避免出现"孤立的房间"
            throw BizException.stateConflict(
                    "顶级节点只能是楼栋或片区，实际为 " + type.label());
        }

        // ★ 序号必须同级唯一：
        //   path_code 由「父级 path_code + 本级两位序号」拼成（物化路径），
        //   若同级序号重复，两个兄弟会得到完全相同的 path_code，
        //   导致「子树前缀匹配」把兄弟也算进来 —— 权限继承、设备归属全都会失准。
        //   因此未显式传 sortNo 时，自动取同级最大值 + 1。
        int seq = cmd.sortNo() != null ? cmd.sortNo() : nextSortNo(cmd.orgId(), cmd.parentId());
        int level = parent == null ? type.defaultLevel()
                : (parent.getSpaceLevel() == null ? 1 : parent.getSpaceLevel()) + 1;

        AssetSpace e = new AssetSpace();
        e.setId(idGen.nextId());
        e.setTenantId(tenantId);
        e.setOrgId(cmd.orgId());
        e.setParentId(cmd.parentId());
        e.setSpaceCode(cmd.spaceCode());
        e.setSpaceName(cmd.spaceName());
        e.setSpaceType(type.name());
        e.setSpacePath(PathCodeUtil.buildSpacePath(
                parent == null ? null : parent.getSpacePath(),
                parent == null ? null : parent.getId()));
        e.setPathCode(PathCodeUtil.build(
                parent == null ? null : parent.getPathCode(), seq));
        e.setSpaceLevel(level);
        e.setFullName(parent == null ? cmd.spaceName()
                : (parent.getFullName() == null ? parent.getSpaceName() : parent.getFullName())
                    + cmd.spaceName());
        e.setArea(cmd.area());
        e.setSortNo(seq);
        e.setLocationCode(cmd.locationCode());
        e.setIsPublic(1);
        e.setStatus("ENABLED");
        e.setIsDeleted(0);

        spaceMapper.insert(e);
        return SpaceVO.from(e);
    }

    @Override
    public SpaceVO get(Long id) {
        AssetSpace e = spaceMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("空间节点");
        }
        return SpaceVO.from(e);
    }

    @Override
    public List<SpaceVO> children(Long parentId) {
        LambdaQueryWrapper<AssetSpace> qw = new LambdaQueryWrapper<AssetSpace>()
                .eq(parentId != null, AssetSpace::getParentId, parentId)
                .orderByAsc(AssetSpace::getPathCode);
        return spaceMapper.selectList(qw).stream().map(SpaceVO::from).toList();
    }

    @Override
    public List<SpaceVO> subtree(Long rootId) {
        AssetSpace root = spaceMapper.selectById(rootId);
        if (root == null) {
            throw BizException.notFound("空间节点");
        }
        // 用 path_code 前缀查子树（天然按前序排序）
        LambdaQueryWrapper<AssetSpace> qw = new LambdaQueryWrapper<AssetSpace>()
                .likeRight(AssetSpace::getPathCode, root.getPathCode())
                .orderByAsc(AssetSpace::getPathCode);
        List<AssetSpace> list = spaceMapper.selectList(qw);
        return buildTree(list);
    }

    @Override
    public List<SpaceVO> treeOfOrg(Long orgId) {
        LambdaQueryWrapper<AssetSpace> qw = new LambdaQueryWrapper<AssetSpace>()
                .eq(AssetSpace::getOrgId, orgId)
                .orderByAsc(AssetSpace::getPathCode);
        return buildTree(spaceMapper.selectList(qw));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void delete(Long id) {
        Long kids = spaceMapper.selectCount(new LambdaQueryWrapper<AssetSpace>()
                .eq(AssetSpace::getParentId, id));
        if (kids != null && kids > 0) {
            throw BizException.stateConflict("存在子节点，不允许删除");
        }
        Long houses = houseMapper.selectCount(new LambdaQueryWrapper<AssetHouse>()
                .eq(AssetHouse::getSpaceId, id));
        if (houses != null && houses > 0) {
            throw BizException.stateConflict("该空间下存在房源，不允许删除");
        }
        if (spaceMapper.deleteById(id) == 0) {
            throw BizException.notFound("空间节点");
        }
    }


    @Override
    public SpaceVO update(Long id, com.yundao.bp.asset.dto.SpaceUpdateCmd cmd) {
        AssetSpace space = spaceMapper.selectById(id);
        if (space == null) {
            throw BizException.notFound("空间节点");
        }
        // 编码唯一（排除自身）
        Long dup = spaceMapper.selectCount(new LambdaQueryWrapper<AssetSpace>()
                .eq(AssetSpace::getSpaceCode, cmd.spaceCode())
                .ne(AssetSpace::getId, id));
        if (dup != null && dup > 0) {
            throw BizException.paramInvalid("空间编码已存在: " + cmd.spaceCode());
        }
        space.setSpaceName(cmd.spaceName());
        space.setSpaceCode(cmd.spaceCode());
        if (cmd.area() != null) {
            space.setArea(cmd.area());
        }
        if (cmd.sortNo() != null) {
            space.setSortNo(cmd.sortNo());
        }
        if (cmd.status() != null && !cmd.status().isBlank()) {
            space.setStatus(cmd.status());
        }
        space.setRemark(cmd.remark());
        // fullName 由父级全名 + 本节点名称组成，改名后同步
        String parentFull = null;
        if (space.getParentId() != null) {
            AssetSpace parent = spaceMapper.selectById(space.getParentId());
            if (parent != null) {
                parentFull = parent.getFullName();
            }
        }
        space.setFullName((parentFull == null || parentFull.isBlank() ? "" : parentFull)
                + cmd.spaceName());
        spaceMapper.updateById(space);
        return get(id);
    }

    // ---------- 内部 ----------


    private SpaceType parseType(String t) {
        try {
            return SpaceType.valueOf(t);
        } catch (Exception e) {
            throw BizException.paramInvalid("未知空间类型: " + t);
        }
    }

    /** 把扁平列表组装成树（按 parentId 建索引，保持 path_code 顺序）。 */
    private List<SpaceVO> buildTree(List<AssetSpace> flat) {
        Map<Long, SpaceVO> byId = new LinkedHashMap<>();
        for (AssetSpace e : flat) {
            byId.put(e.getId(), SpaceVO.from(e));
        }
        Map<Long, List<SpaceVO>> childrenOf = new HashMap<>();
        List<SpaceVO> roots = new ArrayList<>();
        for (AssetSpace e : flat) {
            SpaceVO vo = byId.get(e.getId());
            if (e.getParentId() != null && byId.containsKey(e.getParentId())) {
                childrenOf.computeIfAbsent(e.getParentId(), k -> new ArrayList<>()).add(vo);
            } else {
                roots.add(vo);
            }
        }
        byId.forEach((id, vo) -> {
            List<SpaceVO> kids = childrenOf.get(id);
            if (kids != null) {
                vo.children().addAll(kids);
            }
        });
        return roots;
    }
}
