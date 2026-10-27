package com.yundao.bp.dev.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 设备查询接口。
 *
 * <p><b>补齐说明</b>：此前只有「门锁绑定解析」，没有设备列表接口，
 * 导致前端「设备管理」页无处可查。本控制器只做<b>查询</b>，
 * 设备注册/绑定仍由 IoT 侧与绑定流程负责。
 */
@RestController
@RequestMapping("/api/v1/devices")
public class DeviceController {

    private final DevDeviceMapper mapper;

    /** 房源（继承链起点：房源→空间） */
    private final com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper;

    /** 空间（向上遍历祖先） */
    private final com.yundao.bp.asset.mapper.AssetSpaceMapper spaceMapper;

    private final com.yundao.bp.common.id.SnowflakeIdGenerator idGen;

    public DeviceController(DevDeviceMapper mapper,
                            com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper,
                            com.yundao.bp.asset.mapper.AssetSpaceMapper spaceMapper,
                            com.yundao.bp.common.id.SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.houseMapper = houseMapper;
        this.spaceMapper = spaceMapper;
        this.idGen = idGen;
    }

    /**
     * 分页查询设备。
     *
     * <p>过滤维度按 `bp_dev_device` 实际字段：spaceId / deviceId / deviceMac /
     * onlineStatus。该表<b>没有</b> houseId / lockId 列——门锁与房源的关系
     * 由绑定记录与空间层级推导，不在设备表冗余。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping
    public R<PageResult<DevDevice>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long spaceId,
            @RequestParam(required = false) String deviceId,
            @RequestParam(required = false) String deviceMac,
            @RequestParam(required = false) Integer onlineStatus,
            @RequestParam(required = false) String deviceType,
            @RequestParam(required = false) String keyword) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<DevDevice>()
                .eq(spaceId != null, DevDevice::getSpaceId, spaceId)
                .eq(deviceType != null && !deviceType.isBlank(),
                        DevDevice::getDeviceType, deviceType)
                .eq(deviceId != null && !deviceId.isBlank(),
                        DevDevice::getDeviceId, deviceId)
                .like(deviceMac != null && !deviceMac.isBlank(),
                        DevDevice::getDeviceMac, deviceMac)
                .eq(onlineStatus != null, DevDevice::getOnlineStatus, onlineStatus)
                .and(keyword != null && !keyword.isBlank(),
                        w -> w.like(DevDevice::getDeviceId, keyword)
                                .or().like(DevDevice::getDeviceMac, keyword)
                                .or().like(DevDevice::getDeviceName, keyword))
                .orderByDesc(DevDevice::getId);
        IPage<DevDevice> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return R.ok(PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords()));
    }


    /** 设备分类清单（具体分类 + 大类 + 数量）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/types")
    public R<java.util.List<java.util.Map<String, Object>>> types() {
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (com.yundao.bp.dev.constant.DevDeviceType t
                : com.yundao.bp.dev.constant.DevDeviceType.values()) {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("code", t.name());
            m.put("label", t.label());
            m.put("category", t.category());
            m.put("count", mapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceType, t.name())));
            out.add(m);
        }
        return R.ok(out);
    }

    /** 未绑定任何空间的设备（供绑定弹窗选择）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/unbound")
    public R<java.util.List<DevDevice>> unbound(
            @RequestParam(required = false) String deviceType) {
        return R.ok(mapper.selectList(new LambdaQueryWrapper<DevDevice>()
                .isNull(DevDevice::getSpaceId)
                .eq(deviceType != null && !deviceType.isBlank(),
                        DevDevice::getDeviceType, deviceType)
                .orderByDesc(DevDevice::getId)));
    }

    /**
     * 设备批量导入（CSV）：设备编号, 设备名称, 设备类型, 设备MAC, 房源编号(可空)。
     *
     * <p>逐行导入并返回失败行原因；设备编号重复自动跳过。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:update")
    @PostMapping("/import")
    public R<java.util.Map<String, Object>> importCsv(
            @org.springframework.web.bind.annotation.RequestParam("file")
            org.springframework.web.multipart.MultipartFile file) {
        java.util.List<java.util.Map<String, Object>> errors = new java.util.ArrayList<>();
        int total = 0;
        int created = 0;
        int skipped = 0;
        try (java.io.BufferedReader br = new java.io.BufferedReader(
                new java.io.InputStreamReader(file.getInputStream(),
                        java.nio.charset.StandardCharsets.UTF_8))) {
            String line;
            boolean header = true;
            int lineNo = 0;
            while ((line = br.readLine()) != null) {
                lineNo++;
                if (line.isBlank()) {
                    continue;
                }
                if (line.startsWith("\ufeff")) {
                    line = line.substring(1);
                }
                java.util.List<String> cells = splitCsv(line);
                if (header && (line.contains("设备编号") || line.toLowerCase().contains("deviceid"))) {
                    header = false;
                    continue;
                }
                header = false;
                total++;
                String deviceId = cell(cells, 0);
                String deviceName = cell(cells, 1);
                String typeText = cell(cells, 2);
                String mac = cell(cells, 3);
                String houseCode = cell(cells, 4);
                try {
                    if (deviceId == null) {
                        throw BizException.paramInvalid("设备编号为空");
                    }
                    if (typeText == null) {
                        throw BizException.paramInvalid("设备类型为空");
                    }
                    String deviceType = mapDeviceType(typeText);
                    if (deviceType == null) {
                        throw BizException.paramInvalid("无法识别的设备类型：" + typeText);
                    }
                    Long dup = mapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                            .eq(DevDevice::getDeviceId, deviceId));
                    if (dup != null && dup > 0) {
                        skipped++;
                        java.util.Map<String, Object> e = new java.util.LinkedHashMap<>();
                        e.put("line", lineNo);
                        e.put("message", "设备编号已存在，已跳过：" + deviceId);
                        errors.add(e);
                        continue;
                    }
                    Long spaceId = null;
                    if (houseCode != null) {
                        com.yundao.bp.asset.entity.AssetHouse h = houseMapper.selectOne(
                                new LambdaQueryWrapper<com.yundao.bp.asset.entity.AssetHouse>()
                                        .eq(com.yundao.bp.asset.entity.AssetHouse::getHouseCode, houseCode)
                                        .last("LIMIT 1"));
                        if (h == null) {
                            throw BizException.notFound("房源 " + houseCode);
                        }
                        spaceId = h.getSpaceId();
                    }
                    DevDevice d = new DevDevice();
                    d.setId(idGen.nextId());
                    d.setTenantId(com.yundao.bp.common.tenant.TenantContext.tenantId());
                    d.setDeviceId(deviceId);
                    d.setDeviceName(deviceName == null ? deviceId : deviceName);
                    d.setDeviceType(deviceType);
                    d.setDeviceMac(mac);
                    d.setSpaceId(spaceId);
                    d.setOnlineStatus(0);
                    d.setCreateTime(java.time.LocalDateTime.now());
                    d.setUpdateTime(java.time.LocalDateTime.now());
                    mapper.insert(d);
                    created++;
                } catch (Exception ex) {
                    java.util.Map<String, Object> e = new java.util.LinkedHashMap<>();
                    e.put("line", lineNo);
                    e.put("message", ex.getMessage() == null ? "导入失败" : ex.getMessage());
                    errors.add(e);
                }
            }
        } catch (Exception ex) {
            throw BizException.paramInvalid("文件读取失败：" + ex.getMessage());
        }
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("total", total);
        out.put("created", created);
        out.put("skipped", skipped);
        out.put("errors", errors);
        return R.ok(out);
    }

    private static String cell(java.util.List<String> cells, int i) {
        if (i >= cells.size()) {
            return null;
        }
        String v = cells.get(i);
        if (v == null) {
            return null;
        }
        v = v.trim();
        return v.isEmpty() ? null : v;
    }

    private static java.util.List<String> splitCsv(String line) {
        java.util.List<String> out = new java.util.ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean quoted = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (quoted) {
                if (c == '"' && i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    sb.append('"');
                    i++;
                } else if (c == '"') {
                    quoted = false;
                } else {
                    sb.append(c);
                }
            } else if (c == '"') {
                quoted = true;
            } else if (c == ',') {
                out.add(sb.toString());
                sb.setLength(0);
            } else {
                sb.append(c);
            }
        }
        out.add(sb.toString());
        return out;
    }

    /** 中文类型/英文码 → 设备类型码 */
    private static String mapDeviceType(String text) {
        String t = text.trim();
        java.util.Map<String, String> m = new java.util.LinkedHashMap<>();
        m.put("门锁", "LOCK");
        m.put("智能锁", "LOCK");
        m.put("门禁", "ACCESS");
        m.put("道闸", "BARRIER");
        m.put("摄像头", "CAMERA");
        m.put("视频", "CAMERA");
        m.put("电表", "ELEC_METER");
        m.put("水表", "WATER_METER");
        m.put("燃气表", "GAS_METER");
        m.put("气表", "GAS_METER");
        m.put("传感器", "SENSOR");
        if (m.containsKey(t)) {
            return m.get(t);
        }
        String up = t.toUpperCase();
        for (String code : java.util.List.of("LOCK", "ACCESS", "BARRIER", "CAMERA",
                "ELEC_METER", "WATER_METER", "GAS_METER", "SENSOR")) {
            if (code.equals(up)) {
                return code;
            }
        }
        return null;
    }

    /** 设备绑定/解绑空间：spaceId 传空表示解绑。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:update")
    @org.springframework.web.bind.annotation.PostMapping("/{id:\\d+}/bind")
    public R<DevDevice> bind(@PathVariable Long id,
                             @RequestBody java.util.Map<String, Object> body) {
        DevDevice d = mapper.selectById(id);
        if (d == null) {
            throw BizException.notFound("设备");
        }
        Object raw = body == null ? null : body.get("spaceId");
        if (raw == null || String.valueOf(raw).isBlank()
                || "null".equals(String.valueOf(raw))) {
            // MyBatis-Plus 默认忽略 null 字段，解绑必须显式 set null
            mapper.update(null, new com.baomidou.mybatisplus.core.conditions.update
                    .LambdaUpdateWrapper<DevDevice>()
                    .eq(DevDevice::getId, id)
                    .set(DevDevice::getSpaceId, null)
                    .set(DevDevice::getUpdateTime, java.time.LocalDateTime.now()));
            return R.ok(mapper.selectById(id));
        } else {
            Long spaceId = Long.valueOf(String.valueOf(raw));
            if (spaceMapper.selectById(spaceId) == null) {
                throw BizException.notFound("空间");
            }
            d.setSpaceId(spaceId);
        }
        d.setUpdateTime(java.time.LocalDateTime.now());
        mapper.updateById(d);
        return R.ok(d);
    }

    /**
     * 批量绑定：按「房源编号 + 设备编号」逐行绑定到房源所在空间。
     *
     * <p>逐行返回结果，单行失败不影响其它行。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:update")
    @PostMapping("/bind-batch")
    public R<java.util.Map<String, Object>> bindBatch(
            @RequestBody java.util.List<java.util.Map<String, String>> rows) {
        java.util.List<java.util.Map<String, Object>> results = new java.util.ArrayList<>();
        int ok = 0;
        int line = 0;
        for (java.util.Map<String, String> row : rows == null
                ? java.util.List.<java.util.Map<String, String>>of() : rows) {
            line++;
            String houseCode = row.get("houseCode");
            String deviceNo = row.get("deviceId");
            java.util.Map<String, Object> r = new java.util.LinkedHashMap<>();
            r.put("line", line);
            r.put("houseCode", houseCode);
            r.put("deviceId", deviceNo);
            try {
                if (houseCode == null || houseCode.isBlank()) {
                    throw BizException.paramInvalid("房源编号为空");
                }
                if (deviceNo == null || deviceNo.isBlank()) {
                    throw BizException.paramInvalid("设备编号为空");
                }
                com.yundao.bp.asset.entity.AssetHouse h = houseMapper.selectOne(
                        new LambdaQueryWrapper<com.yundao.bp.asset.entity.AssetHouse>()
                                .eq(com.yundao.bp.asset.entity.AssetHouse::getHouseCode,
                                        houseCode.trim())
                                .last("LIMIT 1"));
                if (h == null) {
                    throw BizException.notFound("房源 " + houseCode);
                }
                if (h.getSpaceId() == null) {
                    throw BizException.stateConflict("房源未关联空间，无法绑定设备");
                }
                DevDevice d = mapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                        .eq(DevDevice::getDeviceId, deviceNo.trim())
                        .last("LIMIT 1"));
                if (d == null) {
                    throw BizException.notFound("设备 " + deviceNo);
                }
                if (d.getSpaceId() != null && !d.getSpaceId().equals(h.getSpaceId())) {
                    throw BizException.stateConflict("该设备已绑定其它空间，请先解绑");
                }
                d.setSpaceId(h.getSpaceId());
                d.setUpdateTime(java.time.LocalDateTime.now());
                mapper.updateById(d);
                r.put("success", true);
                r.put("message", "已绑定到 " + h.getSpaceId());
                ok++;
            } catch (Exception ex) {
                r.put("success", false);
                r.put("message", ex.getMessage() == null ? "绑定失败" : ex.getMessage());
            }
            results.add(r);
        }
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("total", line);
        out.put("success", ok);
        out.put("failed", line - ok);
        out.put("rows", results);
        return R.ok(out);
    }

    /**
     * 空间设备继承：给定房源，沿空间祖先链收集可授权设备。
     *
     * <p><b>统一模型</b>：设备只绑定空间（{@code dev_device.space_id}），
     * 房源通过 {@code house.space_id} 定位；入住人可继承
     * 床位→房间→楼层→单元→楼栋 各级设备，无需"房源设备"概念。
     *
     * <p>返回示例：房间门锁（本房源）、单元门禁（继承）、小区大门（继承）。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/inherited")
    public R<java.util.Map<String, Object>> inherited(@RequestParam Long houseId) {
        com.yundao.bp.asset.entity.AssetHouse house = houseMapper.selectById(houseId);
        if (house == null) {
            throw BizException.notFound("房源");
        }
        java.util.List<com.yundao.bp.asset.entity.AssetSpace> chain = new java.util.ArrayList<>();
        Long sid = house.getSpaceId();
        int guard = 0;
        while (sid != null && guard++ < 8) {
            com.yundao.bp.asset.entity.AssetSpace sp = spaceMapper.selectById(sid);
            if (sp == null) {
                break;
            }
            chain.add(sp);
            sid = sp.getParentId();
        }
        java.util.List<Long> ids = chain.stream().map(com.yundao.bp.asset.entity.AssetSpace::getId)
                .toList();
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetSpace> byId = new java.util.HashMap<>();
        for (com.yundao.bp.asset.entity.AssetSpace sp : chain) {
            byId.put(sp.getId(), sp);
        }
        java.util.List<com.yundao.bp.dev.entity.DevDevice> devices = ids.isEmpty()
                ? java.util.List.of()
                : mapper.selectList(new LambdaQueryWrapper<com.yundao.bp.dev.entity.DevDevice>()
                        .in(com.yundao.bp.dev.entity.DevDevice::getSpaceId, ids));

        java.util.List<java.util.Map<String, Object>> chainOut = new java.util.ArrayList<>();
        for (com.yundao.bp.asset.entity.AssetSpace sp : chain) {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("spaceId", String.valueOf(sp.getId()));
            m.put("spaceCode", sp.getSpaceCode());
            m.put("spaceName", sp.getSpaceName());
            m.put("spaceType", sp.getSpaceType());
            chainOut.add(m);
        }
        java.util.List<java.util.Map<String, Object>> devOut = new java.util.ArrayList<>();
        for (com.yundao.bp.dev.entity.DevDevice d : devices) {
            com.yundao.bp.asset.entity.AssetSpace sp = byId.get(d.getSpaceId());
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("deviceId", d.getDeviceId());
            m.put("deviceName", d.getDeviceName());
            m.put("deviceType", d.getDeviceType());
            m.put("spaceId", d.getSpaceId() == null ? null : String.valueOf(d.getSpaceId()));
            m.put("spaceName", sp == null ? null : sp.getSpaceName());
            m.put("spaceType", sp == null ? null : sp.getSpaceType());
            m.put("scope", house.getSpaceId() != null
                    && house.getSpaceId().equals(d.getSpaceId()) ? "本房源" : "继承");
            m.put("onlineStatus", d.getOnlineStatus());
            devOut.add(m);
        }
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("houseId", String.valueOf(house.getId()));
        out.put("houseCode", house.getHouseCode());
        out.put("houseName", house.getHouseName());
        out.put("chain", chainOut);
        out.put("devices", devOut);
        out.put("total", devOut.size());
        return R.ok(out);
    }

    /** 设备详情。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/{id:\\d+}")
    public R<DevDevice> get(@PathVariable Long id) {
        DevDevice d = mapper.selectById(id);
        if (d == null) {
            throw BizException.notFound("设备");
        }
        return R.ok(d);
    }


    /**
     * 数据新鲜度检查：按上报间隔契约判定设备是否失联。
     *
     * <p>门锁要求 ≥1 天 1 次、水电表 ≥1 天 2 次；传入 hours 可自定义阈值。
     * 用于上线后巡检「数据静默失效」。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/freshness")
    public R<java.util.Map<String, Object>> freshness(
            @RequestParam(defaultValue = "24") int hours) {
        java.time.LocalDateTime deadline = java.time.LocalDateTime.now()
                .minusHours(Math.max(1, hours));
        java.util.List<DevDevice> all = mapper.selectList(new LambdaQueryWrapper<>());
        java.util.List<java.util.Map<String, Object>> stale = new java.util.ArrayList<>();
        int fresh = 0;
        for (DevDevice d : all) {
            java.time.LocalDateTime last = d.getLastReportTime() != null
                    ? d.getLastReportTime()
                    : (d.getUpdateTime() != null ? d.getUpdateTime() : d.getCreateTime());
            boolean ok = last != null && last.isAfter(deadline);
            if (ok) {
                fresh++;
                continue;
            }
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("deviceId", d.getDeviceId());
            m.put("deviceName", d.getDeviceName());
            m.put("deviceType", d.getDeviceType());
            m.put("spaceId", d.getSpaceId() == null ? null : String.valueOf(d.getSpaceId()));
            m.put("lastReportTime", last == null ? null : last.toString());
            m.put("hoursSilent", last == null ? null
                    : java.time.Duration.between(last, java.time.LocalDateTime.now()).toHours());
            m.put("battery", d.getBattery());
            stale.add(m);
        }
        stale.sort((a, b) -> Long.compare(
                ((Number) (b.get("hoursSilent") == null ? 0 : b.get("hoursSilent"))).longValue(),
                ((Number) (a.get("hoursSilent") == null ? 0 : a.get("hoursSilent"))).longValue()));
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("thresholdHours", hours);
        out.put("total", all.size());
        out.put("fresh", fresh);
        out.put("stale", stale.size());
        out.put("staleRate", all.isEmpty() ? 0.0
                : Math.round(stale.size() * 10000.0 / all.size()) / 100.0);
        out.put("staleDevices", stale.size() > 50 ? stale.subList(0, 50) : stale);
        return R.ok(out);
    }

    /** 在线/绑定状态统计（看板用）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/stats")
    public R<java.util.Map<String, Object>> stats() {
        long total = orZero(mapper.selectCount(new LambdaQueryWrapper<>()));
        long online = orZero(mapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getOnlineStatus, 1)));
        java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("total", total);
        m.put("online", online);
        m.put("offline", total - online);
        m.put("onlineRate", total == 0 ? 0.0
                : Math.round(online * 10000.0 / total) / 100.0);
        return R.ok(m);
    }

    private static long orZero(Long v) {
        return v == null ? 0 : v;
    }
}
