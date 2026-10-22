package com.yundao.bp.asset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.asset.constant.HouseStatus;
import com.yundao.bp.asset.constant.SpaceType;
import com.yundao.bp.asset.dto.HouseCreateCmd;
import com.yundao.bp.asset.dto.HouseVO;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.entity.AssetSpace;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.mapper.AssetSpaceMapper;
import com.yundao.bp.asset.service.HouseService;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 房源服务实现。
 */
@Service
public class HouseServiceImpl implements HouseService {

    private final AssetHouseMapper houseMapper;
    private final AssetSpaceMapper spaceMapper;
    private final SnowflakeIdGenerator idGen;

    public HouseServiceImpl(AssetHouseMapper houseMapper, AssetSpaceMapper spaceMapper,
                            SnowflakeIdGenerator idGen) {
        this.houseMapper = houseMapper;
        this.spaceMapper = spaceMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public HouseVO create(HouseCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        // ---- 1) 校验挂载节点：必须存在且为 ROOM / BED ----
        AssetSpace space = spaceMapper.selectById(cmd.spaceId());
        if (space == null) {
            throw BizException.notFound("空间节点");
        }
        SpaceType type;
        try {
            type = SpaceType.valueOf(space.getSpaceType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("空间节点类型非法: " + space.getSpaceType());
        }
        if (!type.canHostHouse()) {
            throw BizException.paramInvalid(
                    "房源只能挂载到 ROOM 或 BED 节点，" + space.getSpaceName()
                            + " 是 " + type.label());
        }

        // ---- 2) 同组织内编码唯一 ----
        Long dup = houseMapper.selectCount(new LambdaQueryWrapper<AssetHouse>()
                .eq(AssetHouse::getOrgId, space.getOrgId())
                .eq(AssetHouse::getHouseCode, cmd.houseCode().trim()));
        if (dup != null && dup > 0) {
            throw new BizException(ErrorCode.DUPLICATED,
                    "房源编号已存在: " + cmd.houseCode().trim());
        }

        // ---- 3) 组装 ----
        long id = idGen.nextId();
        AssetHouse e = new AssetHouse();
        e.setId(id);
        e.setTenantId(tenantId);
        // ★ orgId 从空间节点派生，不采信前端，避免跨组织挂载
        e.setOrgId(space.getOrgId());
        e.setSpaceId(cmd.spaceId());
        e.setHouseCode(cmd.houseCode().trim());
        e.setHouseName(cmd.houseName().trim());
        e.setHouseType(cmd.houseType());
        e.setStructType(blankToNull(cmd.structType()));
        e.setUseType(blankToNull(cmd.useType()));
        e.setUnitLayout(cmd.unitLayout());
        // 楼层号未传时，从空间节点的 space_level 无法推断，留空
        e.setFloorNo(cmd.floorNo());
        e.setOrientation(cmd.orientation());
        // 面积未传时继承空间节点面积（房间节点通常已录面积）
        e.setArea(cmd.area() != null ? cmd.area() : space.getArea());
        e.setInnerArea(cmd.innerArea());
        e.setDecoration(blankToNull(cmd.decoration()));
        e.setSecurityType(blankToNull(cmd.securityType()));
        e.setRentStandard(cmd.rentStandard());
        e.setRentUnit(blankToNull(cmd.rentUnit()));
        e.setMaxCapacity(cmd.maxCapacity());
        e.setCurrentCapacity(0);
        // ---- 4) 初始状态固定为待分配 ----
        e.setHouseStatus(HouseStatus.PENDING_ALLOC.name());
        e.setUseStatus("IDLE");
        e.setManageNature(blankToNull(cmd.manageNature()));
        e.setPropertyNature(blankToNull(cmd.propertyNature()));
        e.setOwnerOrgId(cmd.ownerOrgId());
        e.setAdminOrgId(cmd.adminOrgId());
        e.setHouseAlias(cmd.houseAlias());
        e.setLockStatusTime(LocalDateTime.now());
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);

        houseMapper.insert(e);
        return toVO(e);
    }

    @Override
    public HouseVO get(Long id) {
        AssetHouse e = houseMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("房源");
        }
        return toVO(e);
    }

    @Override
    public PageResult<HouseVO> page(long pageNum, long pageSize, Long orgId,
                                    Long spaceId, String houseStatus, String houseType, String keyword) {
        LambdaQueryWrapper<AssetHouse> qw = new LambdaQueryWrapper<AssetHouse>()
                .eq(orgId != null, AssetHouse::getOrgId, orgId)
                .eq(spaceId != null, AssetHouse::getSpaceId, spaceId)
                .eq(houseStatus != null && !houseStatus.isBlank(),
                        AssetHouse::getHouseStatus, houseStatus)
                .eq(houseType != null && !houseType.isBlank(),
                        AssetHouse::getHouseType, houseType)
                .orderByDesc(AssetHouse::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(AssetHouse::getHouseCode, keyword)
                    .or().like(AssetHouse::getHouseName, keyword));
        }
        IPage<AssetHouse> page = houseMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<HouseVO> rows = page.getRecords().stream().map(this::toVO).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public HouseVO changeStatus(Long id, String targetStatus) {
        HouseStatus target;
        try {
            target = HouseStatus.valueOf(targetStatus);
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("房源状态不合法: " + targetStatus);
        }
        AssetHouse e = houseMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("房源");
        }
        HouseStatus current = HouseStatus.valueOf(e.getHouseStatus());
        if (current == target) {
            return toVO(e);
        }
        if (!HouseStatus.nextOf(current).contains(target)) {
            throw BizException.stateConflict(
                    "房源状态不允许从 " + current.label() + " 变更为 " + target.label());
        }
        e.setHouseStatus(target.name());
        e.setLockStatusTime(LocalDateTime.now());
        houseMapper.updateById(e);
        return toVO(e);
    }

    /**
     * 实体 → 视图。
     *
     * <p>派生指标 {@code vacantDays}（空置天数）：仅对可配租状态
     * （{@link HouseStatus#POOLABLE} = PENDING_ALLOC / VACANT）计算，
     * 从状态变更时间起算；其它状态返回 null（表示"非空置"，而非"空置 0 天"）。
     */
    private HouseVO toVO(AssetHouse e) {
        HouseStatus st;
        try {
            st = HouseStatus.valueOf(e.getHouseStatus());
        } catch (IllegalArgumentException ex) {
            st = HouseStatus.PENDING_ALLOC;
        }
        Long vacantDays = null;
        if (HouseStatus.POOLABLE.contains(st) && e.getLockStatusTime() != null) {
            vacantDays = java.time.temporal.ChronoUnit.DAYS.between(
                    e.getLockStatusTime().toLocalDate(), java.time.LocalDate.now());
        }
        return HouseVO.from(e, st.label(), vacantDays);
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
