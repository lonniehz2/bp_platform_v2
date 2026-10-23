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

    private static final org.slf4j.Logger log =
            org.slf4j.LoggerFactory.getLogger(HouseServiceImpl.class);

    private final AssetHouseMapper houseMapper;
    private final AssetSpaceMapper spaceMapper;
    private final SnowflakeIdGenerator idGen;


    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /**
     * 把当前用户的数据范围追加到查询条件上。
     *
     * @param qw       查询条件
     * @param orgCol   组织列（orgId）
     * @param personCol 人员列（SELF 范围用）
     */
    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            if (scope.personId() == null) {
                qw.eq(orgCol, -1L);      // 未绑定人员：不返回任何数据
            } else {
                qw.eq(personCol, scope.personId());
            }
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }


    /** 组织（导入时按编码定位） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamOrgMapper importOrgMapper;


    /** 空间（批量建床位用） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetSpaceMapper bedSpaceMapper;

    /** 合同（床位租住状态） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizContractMapper bedContractMapper;

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
        applyDataScope(qw, AssetHouse::getOrgId, AssetHouse::getOwnerPersonId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(AssetHouse::getHouseCode, keyword)
                    .or().like(AssetHouse::getHouseName, keyword));
        }
        IPage<AssetHouse> page = houseMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        // 用可变列表：fillSpaceInfo 会回填所属空间（房间/床位）信息
        List<HouseVO> rows = new java.util.ArrayList<>(
                page.getRecords().stream().map(this::toVO).toList());
        fillSpaceInfo(page.getRecords(), rows);
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    /**
     * 批量补房源所属空间（房间/床位）。
     *
     * <p>宿舍（床位 BED）与合租场景下，房源挂在 BED 节点，列表需要显示
     * 「该床位属于哪个房间」，否则运营无法定位。批量查询避免 N+1。
     */
    private void fillSpaceInfo(List<AssetHouse> entities, List<HouseVO> rows) {
        if (spaceMapper == null || entities == null || entities.isEmpty()) {
            return;
        }
        java.util.Set<Long> ids = entities.stream()
                .map(AssetHouse::getSpaceId).filter(java.util.Objects::nonNull)
                .collect(java.util.stream.Collectors.toSet());
        if (ids.isEmpty()) {
            return;
        }
        java.util.Map<Long, AssetSpace> byId = new java.util.HashMap<>();
        for (AssetSpace sp : spaceMapper.selectBatchIds(ids)) {
            byId.put(sp.getId(), sp);
        }
        for (int i = 0; i < entities.size(); i++) {
            AssetSpace sp = byId.get(entities.get(i).getSpaceId());
            if (sp == null) {
                continue;
            }
            HouseVO old = rows.get(i);
            rows.set(i, HouseVO.from(entities.get(i), old.houseStatusLabel(), old.vacantDays(),
                    sp.getSpaceName(), sp.getSpaceType()));
        }
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

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public java.util.Map<String, Object> importCsv(
            org.springframework.web.multipart.MultipartFile file) {
        java.util.List<java.util.Map<String, Object>> errors = new java.util.ArrayList<>();
        int created = 0;
        int skipped = 0;
        int total = 0;
        if (file == null || file.isEmpty()) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("请上传 CSV 文件");
        }
        if (importOrgMapper == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("导入服务未就绪");
        }
        java.util.Map<String, Long> orgByCode = new java.util.HashMap<>();
        for (com.yundao.bp.iam.entity.IamOrg o : importOrgMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>())) {
            if (o.getOrgCode() != null) {
                orgByCode.put(o.getOrgCode(), o.getId());
            }
        }
        java.util.Map<String, com.yundao.bp.asset.entity.AssetSpace> spaceByCode =
                new java.util.HashMap<>();
        for (com.yundao.bp.asset.entity.AssetSpace sp : spaceMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>())) {
            if (sp.getSpaceCode() != null) {
                spaceByCode.put(sp.getSpaceCode(), sp);
            }
        }

        try (java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(
                file.getInputStream(), java.nio.charset.StandardCharsets.UTF_8))) {
            String line;
            int lineNo = 0;
            while ((line = br.readLine()) != null) {
                lineNo++;
                if (line.isBlank()) {
                    continue;
                }
                if (lineNo == 1
                        && line.toLowerCase().replace("_", "").replace("-", "")
                                .contains("housecode")) {
                    continue;   // 表头
                }
                total++;
                String[] c = line.split("[,;]");
                if (c.length < 5) {
                    skipped++;
                    errors.add(err(lineNo, "列数不足（至少 5 列）"));
                    continue;
                }
                String orgCode = c[0].trim();
                String spaceCode = c[1].trim();
                String houseCode = c[2].trim();
                String houseName = c[3].trim();
                String houseType = c[4].trim();
                try {
                    Long orgId = orgByCode.get(orgCode);
                    if (orgId == null) {
                        skipped++;
                        errors.add(err(lineNo, "组织编码不存在：" + orgCode));
                        continue;
                    }
                    com.yundao.bp.asset.entity.AssetSpace sp = spaceByCode.get(spaceCode);
                    if (sp == null) {
                        skipped++;
                        errors.add(err(lineNo, "空间编码不存在：" + spaceCode));
                        continue;
                    }
                    if (!sp.getOrgId().equals(orgId)) {
                        skipped++;
                        errors.add(err(lineNo, "空间不属于该组织：" + spaceCode));
                        continue;
                    }
                    Long dup = houseMapper.selectCount(
                            new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                    <com.yundao.bp.asset.entity.AssetHouse>()
                                    .eq(com.yundao.bp.asset.entity.AssetHouse::getHouseCode,
                                            houseCode));
                    if (dup != null && dup > 0) {
                        skipped++;
                        errors.add(err(lineNo, "房源编号已存在：" + houseCode));
                        continue;
                    }
                    com.yundao.bp.asset.entity.AssetHouse e =
                            new com.yundao.bp.asset.entity.AssetHouse();
                    e.setId(idGen.nextId());
                    e.setTenantId(com.yundao.bp.common.tenant.TenantContext.tenantId());
                    e.setOrgId(orgId);
                    e.setSpaceId(sp.getId());
                    e.setHouseCode(houseCode);
                    e.setHouseName(houseName);
                    e.setHouseType(houseType.isBlank() ? "PUBLIC_RENTAL" : houseType);
                    e.setUseType(c.length > 5 && !c[5].isBlank() ? c[5].trim() : "CIVIL");
                    if (c.length > 6 && !c[6].isBlank()) {
                        e.setArea(new java.math.BigDecimal(c[6].trim()));
                    }
                    if (c.length > 7 && !c[7].isBlank()) {
                        e.setRentStandard(new java.math.BigDecimal(c[7].trim()));
                    }
                    e.setRentUnit(c.length > 8 && !c[8].isBlank() ? c[8].trim() : "AREA_MONTH");
                    e.setHouseStatus(c.length > 9 && !c[9].isBlank() ? c[9].trim() : "VACANT");
                    e.setCurrentCapacity(0);
                    e.setIsDeleted(0);
                    e.setCreateTime(java.time.LocalDateTime.now());
                    houseMapper.insert(e);
                    created++;
                } catch (Exception ex) {
                    skipped++;
                    errors.add(err(lineNo, ex.getMessage()));
                }
            }
        } catch (java.io.IOException ex) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("读取文件失败：" + ex.getMessage());
        }

        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("total", total);
        out.put("created", created);
        out.put("skipped", skipped);
        out.put("errors", errors.size() > 100 ? errors.subList(0, 100) : errors);
        log.info("房源导入完成：共 {} 行，成功 {}，跳过 {}", total, created, skipped);
        return out;
    }

    private java.util.Map<String, Object> err(int line, String message) {
        java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("line", line);
        m.put("message", message);
        return m;
    }

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public int batchCreateBeds(Long roomSpaceId, int count,
                               java.math.BigDecimal rentStandard,
                               java.math.BigDecimal areaPerBed) {
        if (roomSpaceId == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("房间不能为空");
        }
        if (count <= 0 || count > 20) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("单次生成床位数量需在 1~20 之间");
        }
        com.yundao.bp.asset.entity.AssetSpace room = spaceMapper.selectById(roomSpaceId);
        if (room == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("房间");
        }
        if (!"ROOM".equals(room.getSpaceType())) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid(
                    "只能在房间（ROOM）下生成床位，当前为 " + room.getSpaceType());
        }
        int created = 0;
        for (int i = 1; i <= count; i++) {
            String bedCode = room.getSpaceCode() + "-B" + i;
            com.yundao.bp.asset.entity.AssetSpace exist = bedSpaceMapper.selectOne(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                            <com.yundao.bp.asset.entity.AssetSpace>()
                            .eq(com.yundao.bp.asset.entity.AssetSpace::getSpaceCode, bedCode)
                            .last("LIMIT 1"));
            if (exist != null) {
                continue;
            }
            com.yundao.bp.asset.entity.AssetSpace bed =
                    new com.yundao.bp.asset.entity.AssetSpace();
            bed.setId(idGen.nextId());
            bed.setTenantId(com.yundao.bp.common.tenant.TenantContext.tenantId());
            bed.setOrgId(room.getOrgId());
            bed.setParentId(room.getId());
            bed.setSpaceCode(bedCode);
            bed.setSpaceName(room.getSpaceName() + " 床位" + i);
            bed.setSpaceType("BED");
            bed.setArea(areaPerBed);
            bed.setSortNo(i);
            bed.setIsDeleted(0);
            bed.setCreateTime(java.time.LocalDateTime.now());
            spaceMapper.insert(bed);

            com.yundao.bp.asset.entity.AssetHouse h = new com.yundao.bp.asset.entity.AssetHouse();
            h.setId(idGen.nextId());
            h.setTenantId(com.yundao.bp.common.tenant.TenantContext.tenantId());
            h.setOrgId(room.getOrgId());
            h.setSpaceId(bed.getId());
            h.setHouseCode(bedCode);
            h.setHouseName(room.getSpaceName() + " 床位" + i);
            h.setHouseType("DORMITORY");
            h.setUseType("CIVIL");
            h.setRentUnit("BED_MONTH");
            h.setRentStandard(rentStandard);
            h.setArea(areaPerBed);
            h.setHouseStatus("VACANT");
            h.setCurrentCapacity(0);
            h.setMaxCapacity(1);
            h.setIsDeleted(0);
            h.setCreateTime(java.time.LocalDateTime.now());
            houseMapper.insert(h);
            created++;
        }
        log.info("房间 {} 批量生成床位：请求 {}，实际新建 {}", room.getSpaceCode(), count, created);
        return created;
    }

    @Override
    public java.util.List<java.util.Map<String, Object>> listBeds(Long roomSpaceId) {
        if (roomSpaceId == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("房间不能为空");
        }
        java.util.List<com.yundao.bp.asset.entity.AssetSpace> beds = bedSpaceMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        <com.yundao.bp.asset.entity.AssetSpace>()
                        .eq(com.yundao.bp.asset.entity.AssetSpace::getParentId, roomSpaceId)
                        .eq(com.yundao.bp.asset.entity.AssetSpace::getSpaceType, "BED")
                        .orderByAsc(com.yundao.bp.asset.entity.AssetSpace::getSortNo));
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (com.yundao.bp.asset.entity.AssetSpace bed : beds) {
            com.yundao.bp.asset.entity.AssetHouse h = houseMapper.selectOne(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                            <com.yundao.bp.asset.entity.AssetHouse>()
                            .eq(com.yundao.bp.asset.entity.AssetHouse::getSpaceId, bed.getId())
                            .last("LIMIT 1"));
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("spaceId", String.valueOf(bed.getId()));
            m.put("bedCode", bed.getSpaceCode());
            m.put("bedName", bed.getSpaceName());
            m.put("houseId", h == null ? null : String.valueOf(h.getId()));
            m.put("houseStatus", h == null ? "NO_HOUSE" : h.getHouseStatus());
            m.put("rentStandard", h == null ? null : h.getRentStandard());
            String occupant = null;
            if (h != null && bedContractMapper != null) {
                com.yundao.bp.biz.entity.BizContract c = bedContractMapper.selectOne(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                <com.yundao.bp.biz.entity.BizContract>()
                                .eq(com.yundao.bp.biz.entity.BizContract::getHouseId, h.getId())
                                .in(com.yundao.bp.biz.entity.BizContract::getContractStatus,
                                        java.util.List.of("EFFECTIVE", "RENEWING"))
                                .last("LIMIT 1"));
                if (c != null) {
                    occupant = c.getLesseeName() != null ? c.getLesseeName() : null;
                    m.put("contractNo", c.getContractNo());
                    m.put("leaseEnd", c.getLeaseEnd() == null ? null
                            : c.getLeaseEnd().toString());
                }
            }
            m.put("occupant", occupant);
            m.put("occupied", occupant != null);
            out.add(m);
        }
        return out;
    }
}
