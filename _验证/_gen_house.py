# -*- coding: utf-8 -*-
"""生成房源创建接口"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ============================================================
FILES['asset/dto/HouseCreateCmd.java'] = '''package com.yundao.bp.asset.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

/**
 * 创建房源。
 *
 * <p><b>关键约束</b>：
 * <ul>
 *   <li>{@code spaceId} 必须是 <b>ROOM 或 BED</b> 类型的空间节点
 *       （{@code SpaceType.canHostHouse()}），否则拒绝 —— 防止把房源挂到楼栋/单元上</li>
 *   <li>{@code orgId} <b>不由前端传入</b>，从 {@code spaceId} 对应的空间节点派生，
 *       避免跨组织挂载</li>
 *   <li>{@code houseCode} 在同一组织内唯一</li>
 *   <li>初始状态固定为 {@code PENDING_ALLOC}（待分配），已入住人数 0</li>
 * </ul>
 *
 * <p>枚举取值（与 DDL 注释一致）：
 * <pre>
 * houseType      PUBLIC_RENTAL 公租房 / AFFORDABLE_RENTAL 保租房 / TALENT 人才公寓 /
 *                APARTMENT 公寓 / DORMITORY 宿舍 / RENTAL 出租房 / HOTEL 酒店民宿
 * structType     VILLA / MULTI / SMALL_HIGH / HIGH / SUPER_HIGH
 * useType        CIVIL 民用 / COMMERCIAL 商用
 * decoration     ROUGH 毛坯 / SIMPLE 简装 / FINE 精装
 * securityType   LOW_RENT 廉租 / PUBLIC 公租 / AFFORDABLE 保租 / TALENT 人才
 * rentUnit       AREA_MONTH 元/㎡·月 / HOUSE_MONTH 元/套·月 / BED_MONTH 元/床·月 / HOUSE_NIGHT 元/套·夜
 * manageNature   SELF 自营 / ENTRUST 委托 / LEASE 租赁
 * propertyNature STATE 国有 / COLLECTIVE 集体 / PRIVATE 私有
 * </pre>
 */
public record HouseCreateCmd(

        @NotNull(message = "关联空间节点不能为空")
        Long spaceId,

        @NotBlank(message = "房源编号不能为空")
        @Size(max = 64, message = "房源编号不能超过 64 字符")
        String houseCode,

        @NotBlank(message = "房源名称不能为空")
        @Size(max = 128, message = "房源名称不能超过 128 字符")
        String houseName,

        @NotBlank(message = "房源类型不能为空")
        @Pattern(regexp = "PUBLIC_RENTAL|AFFORDABLE_RENTAL|TALENT|APARTMENT|DORMITORY|RENTAL|HOTEL",
                message = "房源类型不合法")
        String houseType,

        @Pattern(regexp = "^$|VILLA|MULTI|SMALL_HIGH|HIGH|SUPER_HIGH", message = "建筑类型不合法")
        String structType,

        @Pattern(regexp = "^$|CIVIL|COMMERCIAL", message = "用途不合法")
        String useType,

        @Size(max = 30, message = "户型不能超过 30 字符")
        String unitLayout,

        Integer floorNo,

        @Size(max = 20, message = "朝向不能超过 20 字符")
        String orientation,

        @DecimalMin(value = "0.01", message = "建筑面积必须大于 0")
        BigDecimal area,

        @DecimalMin(value = "0.01", message = "套内面积必须大于 0")
        BigDecimal innerArea,

        @Pattern(regexp = "^$|ROUGH|SIMPLE|FINE", message = "装修标准不合法")
        String decoration,

        @Pattern(regexp = "^$|LOW_RENT|PUBLIC|AFFORDABLE|TALENT", message = "保障类别不合法")
        String securityType,

        @DecimalMin(value = "0", message = "租金标准不能为负")
        BigDecimal rentStandard,

        @Pattern(regexp = "^$|AREA_MONTH|HOUSE_MONTH|BED_MONTH|HOUSE_NIGHT", message = "租金计价单位不合法")
        String rentUnit,

        @Min(value = 1, message = "最大入住人数至少为 1")
        Integer maxCapacity,

        @Pattern(regexp = "^$|SELF|ENTRUST|LEASE", message = "经营性质不合法")
        String manageNature,

        @Pattern(regexp = "^$|STATE|COLLECTIVE|PRIVATE", message = "产权性质不合法")
        String propertyNature,

        Long ownerOrgId,
        Long adminOrgId,

        @Size(max = 64, message = "房源别名不能超过 64 字符")
        String houseAlias,

        @Size(max = 500, message = "备注不能超过 500 字符")
        String remark
) {
}
'''

# ============================================================
FILES['asset/service/HouseService.java'] = '''package com.yundao.bp.asset.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.asset.dto.HouseCreateCmd;
import com.yundao.bp.asset.dto.HouseVO;

/**
 * 房源服务。
 */
public interface HouseService {

    /**
     * 创建房源。
     *
     * <p>自动完成：校验挂载节点（仅 ROOM/BED）、派生 orgId、同组织编码唯一、
     * 初始状态 {@code PENDING_ALLOC}、已入住人数 0。
     */
    HouseVO create(HouseCreateCmd cmd);

    HouseVO get(Long id);

    PageResult<HouseVO> page(long pageNum, long pageSize, Long orgId,
                             Long spaceId, String houseStatus, String keyword);

    HouseVO changeStatus(Long id, String targetStatus);
}
'''

# ============================================================
FILES['asset/service/impl/HouseServiceImpl.java'] = '''package com.yundao.bp.asset.service.impl;

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
                                    Long spaceId, String houseStatus, String keyword) {
        LambdaQueryWrapper<AssetHouse> qw = new LambdaQueryWrapper<AssetHouse>()
                .eq(orgId != null, AssetHouse::getOrgId, orgId)
                .eq(spaceId != null, AssetHouse::getSpaceId, spaceId)
                .eq(houseStatus != null && !houseStatus.isBlank(),
                        AssetHouse::getHouseStatus, houseStatus)
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

    private HouseVO toVO(AssetHouse e) {
        return HouseVO.of(e);
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
'''

# ============================================================
FILES['asset/controller/HouseController.java'] = '''package com.yundao.bp.asset.controller;

import com.yundao.bp.asset.dto.HouseCreateCmd;
import com.yundao.bp.asset.dto.HouseVO;
import com.yundao.bp.asset.service.HouseService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 房源接口（BC-02 空间资产）。
 *
 * <p>创建约束：只能挂到 ROOM / BED 节点；{@code orgId} 由服务端从空间节点派生。
 */
@RestController
@RequestMapping("/api/v1/houses")
public class HouseController {

    private final HouseService houseService;

    public HouseController(HouseService houseService) {
        this.houseService = houseService;
    }

    @PostMapping
    public R<HouseVO> create(@Valid @RequestBody HouseCreateCmd cmd) {
        return R.ok(houseService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<HouseVO> get(@PathVariable Long id) {
        return R.ok(houseService.get(id));
    }

    @GetMapping
    public R<PageResult<HouseVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                       @RequestParam(defaultValue = "20") long pageSize,
                                       @RequestParam(required = false) Long orgId,
                                       @RequestParam(required = false) Long spaceId,
                                       @RequestParam(required = false) String houseStatus,
                                       @RequestParam(required = false) String keyword) {
        return R.ok(houseService.page(pageNum, pageSize, orgId, spaceId, houseStatus, keyword));
    }

    @PostMapping("/{id}/status")
    public R<HouseVO> changeStatus(@PathVariable Long id, @RequestBody StatusCmd cmd) {
        return R.ok(houseService.changeStatus(id, cmd.status()));
    }

    public record StatusCmd(String status) {
    }
}
'''

# ============================================================
count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  ' + ('新增' if rel in ('asset/dto/HouseCreateCmd.java',) else '覆盖') + ' ' + rel)
print('\n共 %d 个文件' % count)
