# -*- coding: utf-8 -*-
"""设备批量导入接口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'dev',
                 'controller', 'DeviceController.java')
s = io.open(p, encoding='utf-8').read()

if 'devices/import' not in s and '/import' not in s:
    # 构造器注入 idGen
    s = s.replace('''    public DeviceController(DevDeviceMapper mapper,
                            com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper,
                            com.yundao.bp.asset.mapper.AssetSpaceMapper spaceMapper) {''',
                  '''    private final com.yundao.bp.common.id.SnowflakeIdGenerator idGen;

    public DeviceController(DevDeviceMapper mapper,
                            com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper,
                            com.yundao.bp.asset.mapper.AssetSpaceMapper spaceMapper,
                            com.yundao.bp.common.id.SnowflakeIdGenerator idGen) {''', 1)
    s = s.replace('''        this.spaceMapper = spaceMapper;
    }''', '''        this.spaceMapper = spaceMapper;
        this.idGen = idGen;
    }''', 1)

    method = '''    /**
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
                if (line.startsWith("\\ufeff")) {
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

'''
    s = s.replace('''    /** 设备绑定/解绑空间：spaceId 传空表示解绑。 */''',
                  method + '''    /** 设备绑定/解绑空间：spaceId 传空表示解绑。 */''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('设备导入接口已加')
else:
    print('已存在导入接口')
