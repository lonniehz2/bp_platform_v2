# -*- coding: utf-8 -*-
"""宿舍床位管理：按房间批量生成床位房源 + 床位视图。

接口：
  POST /houses/beds/batch-create  {roomSpaceId, count, rentStandard, areaPerBed}
       为指定房间生成 N 个床位（BED 空间 + 挂在其上的房源），已存在的床位跳过
  GET  /houses/beds?roomSpaceId=
       列出房间下所有床位及其租住状态（含在租人）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'asset')

# ---------- Service 接口 ----------
S = os.path.join(J, 'service', 'HouseService.java')
s = io.open(S, encoding='utf-8').read()
if 'batchCreateBeds' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 为房间批量生成床位房源，返回新建数量。 */
    int batchCreateBeds(Long roomSpaceId, int count,
                        java.math.BigDecimal rentStandard, java.math.BigDecimal areaPerBed);

    /** 房间下的床位列表（含租住状态与在租人）。 */
    java.util.List<java.util.Map<String, Object>> listBeds(Long roomSpaceId);
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('HouseService：床位接口已加')

# ---------- 实现 ----------
I = os.path.join(J, 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'batchCreateBeds' not in s:
    inject = '''
    /** 空间（批量建床位用） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetSpaceMapper bedSpaceMapper;

    /** 合同（床位租住状态） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizContractMapper bedContractMapper;
'''
    if 'bedSpaceMapper' not in s:
        j = s.find('    public HouseServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]

    impl = '''
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
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('HouseServiceImpl：床位批量生成与视图已实现')

# ---------- Controller ----------
C = os.path.join(J, 'controller', 'HouseController.java')
s = io.open(C, encoding='utf-8').read()
if 'batchCreateBeds' not in s:
    block = '''
    /** 宿舍：为房间批量生成床位房源。 */
    @PostMapping("/beds/batch-create")
    @com.yundao.bp.iam.security.RequirePerm("asset:house:create")
    public R<Integer> batchCreateBeds(@RequestBody BedBatchCmd cmd) {
        return R.ok(houseService.batchCreateBeds(cmd.roomSpaceId(), cmd.count(),
                cmd.rentStandard(), cmd.areaPerBed()));
    }

    /** 宿舍：房间下的床位视图（含在租人）。 */
    @GetMapping("/beds")
    public R<java.util.List<java.util.Map<String, Object>>> listBeds(
            @RequestParam Long roomSpaceId) {
        return R.ok(houseService.listBeds(roomSpaceId));
    }

    public record BedBatchCmd(Long roomSpaceId, int count,
                              java.math.BigDecimal rentStandard,
                              java.math.BigDecimal areaPerBed) {
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + block + s[i:]
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('HouseController：床位接口已加')

print('完成')
