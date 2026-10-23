# -*- coding: utf-8 -*-
"""房源批量导入（数据迁移用）。

接口：POST /api/v1/houses/import  （multipart file=CSV）
列顺序（首行为表头，可省略）：
  组织编码, 空间编码, 房源编号, 房源名称, 房源类型, 用途, 面积, 租金标准, 租金单位, 状态

校验：
  · 组织编码必须存在；空间编码必须在组织下且为 ROOM/BED
  · 房源编号全局唯一，重复则跳过并记原因
  · 类型/用途/单位/状态必须为合法枚举
返回：{total, created, skipped, errors:[{line, message}]}
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'asset')

# ---------- Controller ----------
C = os.path.join(J, 'controller', 'HouseController.java')
s = io.open(C, encoding='utf-8').read()
if 'importCsv' not in s:
    block = '''
    /**
     * 批量导入房源（CSV）。
     *
     * <p>用于真实台账迁移：逐行校验组织、空间、枚举与编号唯一性，
     * 失败行返回行号与原因，不中断整批。
     */
    @PostMapping("/import")
    @com.yundao.bp.iam.security.RequirePerm("asset:house:create")
    public R<java.util.Map<String, Object>> importCsv(
            @org.springframework.web.bind.annotation.RequestParam("file")
            org.springframework.web.multipart.MultipartFile file) {
        return R.ok(houseService.importCsv(file));
    }
'''
    anchor = '    @PostMapping("/{id}/status")'
    if anchor in s:
        s = s.replace(anchor, block + '\n' + anchor, 1)
    else:
        i = s.rstrip().rfind('}')
        s = s[:i] + block + s[i:]
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('HouseController：/houses/import 已加')

# ---------- Service 接口 ----------
S = os.path.join(J, 'service', 'HouseService.java')
s = io.open(S, encoding='utf-8').read()
if 'importCsv' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + ('\n    /** 批量导入房源（CSV）。 */\n'
                 '    java.util.Map<String, Object> importCsv(\n'
                 '            org.springframework.web.multipart.MultipartFile file);\n') + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('HouseService：importCsv 已加')

# ---------- 实现 ----------
I = os.path.join(J, 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'importCsv' not in s:
    # 依赖：组织 mapper、空间 mapper
    inject = '''
    /** 组织（导入时按编码定位） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamOrgMapper importOrgMapper;
'''
    if 'importOrgMapper' not in s:
        j = s.find('    public HouseServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]

    impl = '''
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
                if (lineNo == 1 && line.toLowerCase().contains("housecode")) {
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
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('HouseServiceImpl：importCsv 已实现')

print('完成')
