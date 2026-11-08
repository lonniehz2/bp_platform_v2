package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

/**
 * 设备绑定批量导入：沿用旧系统一张长表的结构。
 *
 * <p>一行一台设备；同一空间多行自动归并。表头：
 * 组织编码,楼栋,单元,楼层,房间,床位内房,房源编号,房源名称,房源类型,建筑面积,
 * 设备编号,设备类型,设备名称,物理MAC。
 *
 * <p>规则：组织编码必须是当前租户项目编码；楼栋/单元/楼层/房间/床位逐级创建；
 * 房间存在时自动创建房源；房源编号为空自动生成；设备编号为空生成 DV 编号；
 * 设备编号重复时同空间跳过、跨空间报错；物理 MAC 不允许重复。
 */
@Service
public class DeviceImportService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    private static final Map<String, String> HOUSE_TYPES = new HashMap<>();
    private static final Map<String, String> DEVICE_TYPES = new HashMap<>();

    static {
        HOUSE_TYPES.put("PUBLIC_RENTAL", "PUBLIC_RENTAL");
        HOUSE_TYPES.put("公租房", "PUBLIC_RENTAL");
        HOUSE_TYPES.put("公共租赁", "PUBLIC_RENTAL");
        HOUSE_TYPES.put("AFFORDABLE_RENTAL", "AFFORDABLE_RENTAL");
        HOUSE_TYPES.put("保障性租赁住房", "AFFORDABLE_RENTAL");
        HOUSE_TYPES.put("保租房", "AFFORDABLE_RENTAL");
        HOUSE_TYPES.put("TALENT_APARTMENT", "TALENT_APARTMENT");
        HOUSE_TYPES.put("人才公寓", "TALENT_APARTMENT");
        HOUSE_TYPES.put("DORMITORY", "DORMITORY");
        HOUSE_TYPES.put("宿舍", "DORMITORY");
        HOUSE_TYPES.put("RENTAL", "RENTAL");
        HOUSE_TYPES.put("出租房", "RENTAL");
        HOUSE_TYPES.put("HOTEL", "HOTEL");
        HOUSE_TYPES.put("酒店民宿", "HOTEL");

        for (String code : List.of("LOCK", "ACCESS", "BARRIER", "ELEVATOR", "WATER_METER",
                "ELEC_METER", "GAS_METER", "HEAT_METER", "CAMERA", "SENSOR", "CAR_LOCK",
                "CONTROLLER", "OTHER")) {
            DEVICE_TYPES.put(code, code);
        }
        DEVICE_TYPES.put("门锁", "LOCK");
        DEVICE_TYPES.put("智能锁", "LOCK");
        DEVICE_TYPES.put("门禁", "ACCESS");
        DEVICE_TYPES.put("道闸", "BARRIER");
        DEVICE_TYPES.put("电梯", "ELEVATOR");
        DEVICE_TYPES.put("水表", "WATER_METER");
        DEVICE_TYPES.put("电表", "ELEC_METER");
        DEVICE_TYPES.put("燃气表", "GAS_METER");
        DEVICE_TYPES.put("气表", "GAS_METER");
        DEVICE_TYPES.put("热量表", "HEAT_METER");
        DEVICE_TYPES.put("摄像头", "CAMERA");
        DEVICE_TYPES.put("视频", "CAMERA");
        DEVICE_TYPES.put("传感器", "SENSOR");
        DEVICE_TYPES.put("车锁", "CAR_LOCK");
        DEVICE_TYPES.put("控制主机", "CONTROLLER");
        DEVICE_TYPES.put("其他", "OTHER");
    }

    public DeviceImportService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public Map<String, Object> importCsv(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw BizException.param("请上传 CSV 文件");
        }
        String tenant = TenantContext.require();
        Map<String, Map<String, Object>> orgByCode = new HashMap<>();
        for (Map<String, Object> org : jdbc.queryForList(
                "select id, org_code orgCode, default_asset_type_code defaultAssetTypeCode, "
                        + "space_template_id spaceTemplateId, business_mode businessMode "
                        + "from bp_org where tenant_id=? and is_deleted=0",
                tenant)) {
            orgByCode.put(String.valueOf(org.get("orgCode")), org);
        }

        List<Map<String, Object>> errors = new ArrayList<>();
        Map<String, Long> spaceCache = new HashMap<>();
        Map<Long, Long> houseCache = new HashMap<>();
        int total = 0, spacesCreated = 0, housesCreated = 0, devicesCreated = 0, devicesBound = 0;
        int[] counters = new int[2];

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                file.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            int lineNo = 0;
            while ((line = reader.readLine()) != null) {
                lineNo++;
                line = line.replace("\ufeff", "");
                if (line.isBlank() || line.startsWith("#")) continue;
                if (lineNo == 1 && (line.contains("组织编码") || line.toLowerCase().contains("orgcode"))) {
                    continue;
                }
                total++;
                String[] c = split(line);
                if (c.length < 9) {
                    errors.add(err(lineNo, "列数不足，至少需要 9 列"));
                    continue;
                }
                String orgCode = v(c, 0);
                String building = v(c, 1);
                String unit = v(c, 2);
                String floor = v(c, 3);
                String room = v(c, 4);
                String bed = v(c, 5);
                String houseCode = v(c, 6);
                String houseName = v(c, 7);
                String houseType = v(c, 8);
                String areaText = v(c, 9);
                String deviceCode = v(c, 10);
                String deviceTypeText = v(c, 11);
                String deviceName = v(c, 12);
                String mac = v(c, 13);
                try {
                    Map<String, Object> org = orgByCode.get(orgCode);
                    if (org == null) throw new IllegalArgumentException("组织编码不存在：" + orgCode);
                    long projectId = ((Number) org.get("id")).longValue();

                    Long parentId = null;
                    Map<String, Object> parent = null;
                    if (!building.isBlank()) {
                        parent = ensureSpace(tenant, projectId, org, null, "BUILDING", building, spaceCache, counters);
                        parentId = ((Number) parent.get("id")).longValue();
                    }
                    if (!unit.isBlank()) {
                        requireParent(parent, "单元", "楼栋");
                        parent = ensureSpace(tenant, projectId, org, parentId, "UNIT", unit, spaceCache, counters);
                        parentId = ((Number) parent.get("id")).longValue();
                    }
                    if (!floor.isBlank()) {
                        requireParent(parent, "楼层", "单元");
                        parent = ensureSpace(tenant, projectId, org, parentId, "FLOOR", floor, spaceCache, counters);
                        parentId = ((Number) parent.get("id")).longValue();
                    }
                    if (!room.isBlank()) {
                        requireParent(parent, "房间", "楼层");
                        parent = ensureSpace(tenant, projectId, org, parentId, "ROOM", room, spaceCache, counters);
                        parentId = ((Number) parent.get("id")).longValue();
                    }
                    if (!bed.isBlank()) {
                        requireParent(parent, "床位/内房", "房间");
                        parent = ensureSpace(tenant, projectId, org, parentId, "BED", bed, spaceCache, counters);
                        parentId = ((Number) parent.get("id")).longValue();
                    }

                    Long houseId = null;
                    if (!room.isBlank() && parent != null) {
                        houseId = ensureHouse(tenant, projectId, parent, houseCode, houseName,
                                houseType, areaText, houseCache, counters);
                    }

                    if (!deviceTypeText.isBlank() || !deviceCode.isBlank() || !mac.isBlank()) {
                        if (parent == null) throw new IllegalArgumentException("设备行必须填写空间节点");
                        String deviceType = DEVICE_TYPES.get(deviceTypeText);
                        if (deviceType == null) {
                            throw new IllegalArgumentException("无法识别的设备类型：" + deviceTypeText);
                        }
                        boolean created = ensureDevice(tenant, projectId,
                                ((Number) parent.get("id")).longValue(), deviceCode, deviceType,
                                deviceName, mac);
                        if (created) devicesCreated++;
                        devicesBound++;
                    }
                } catch (Exception e) {
                    errors.add(err(lineNo, e.getMessage() == null ? "导入失败" : e.getMessage()));
                }
            }
        } catch (Exception e) {
            throw BizException.param("CSV 读取失败：" + e.getMessage());
        }

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("total", total);
        out.put("spacesCreated", counters[0]);
        out.put("housesCreated", counters[1]);
        out.put("devicesCreated", devicesCreated);
        out.put("devicesBound", devicesBound);
        out.put("failed", errors.size());
        out.put("errors", errors);
        return out;
    }

    private Map<String, Object> ensureSpace(String tenant, long projectId, Map<String, Object> org,
                                            Long parentId, String type, String name,
                                            Map<String, Long> cache, int[] counters) {
        String key = projectId + "|" + (parentId == null ? "root" : parentId) + "|" + type + "|" + name;
        Long cached = cache.get(key);
        if (cached != null) {
            return spaceRow(tenant, projectId, cached);
        }
        List<Map<String, Object>> exists = jdbc.queryForList(
                "select id, space_path spacePath, level_no levelNo from bp_space "
                        + "where tenant_id=? and org_id=? and parent_id <=> ? and space_type=? "
                        + "and space_name=? and is_deleted=0",
                tenant, projectId, parentId, type, name);
        if (exists.size() > 1) {
            throw new IllegalArgumentException("空间节点重名，无法唯一确定：" + name);
        }
        if (exists.size() == 1) {
            Long id = ((Number) exists.get(0).get("id")).longValue();
            cache.put(key, id);
            return exists.get(0);
        }
        long id = idGen.nextId();
        String code = "SP" + id;
        int levelNo = 1;
        String path = "/" + code;
        if (parentId != null) {
            Map<String, Object> p = jdbc.queryForMap(
                    "select level_no levelNo, space_path spacePath from bp_space "
                            + "where id=? and tenant_id=? and org_id=? and is_deleted=0",
                    parentId, tenant, projectId);
            levelNo = ((Number) p.get("levelNo")).intValue() + 1;
            path = String.valueOf(p.get("spacePath")) + "/" + code;
        }
        jdbc.update("insert into bp_space(id,tenant_id,org_id,parent_id,space_code,space_name,"
                        + "space_type,space_path,level_no,asset_type_code,space_template_id,business_mode,"
                        + "status,is_deleted) values(?,?,?,?,?,?,?,?,?,?,?,?, 'ENABLED',0)",
                id, tenant, projectId, parentId, code, name, type, path, levelNo,
                org.get("defaultAssetTypeCode"), org.get("spaceTemplateId"), org.get("businessMode"));
        counters[0]++;
        cache.put(key, id);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("spacePath", path);
        out.put("levelNo", levelNo);
        return out;
    }

    private Map<String, Object> spaceRow(String tenant, long projectId, long id) {
        return jdbc.queryForMap("select id, space_path spacePath, level_no levelNo from bp_space "
                + "where id=? and tenant_id=? and org_id=? and is_deleted=0", id, tenant, projectId);
    }

    private Long ensureHouse(String tenant, long projectId, Map<String, Object> leaf,
                             String houseCode, String houseName, String houseType, String areaText,
                             Map<Long, Long> cache, int[] counters) {
        long spaceId = ((Number) leaf.get("id")).longValue();
        Long cached = cache.get(spaceId);
        if (cached != null) return cached;
        List<Long> exists = jdbc.queryForList(
                "select id from bp_house where tenant_id=? and org_id=? and space_id=? and is_deleted=0",
                Long.class, tenant, projectId, spaceId);
        if (exists.size() > 1) throw new IllegalArgumentException("该空间已关联多个房源，请先清理：" + leaf.get("spacePath"));
        if (exists.size() == 1) {
            cache.put(spaceId, exists.get(0));
            return exists.get(0);
        }
        String type = houseType == null || houseType.isBlank() ? null : HOUSE_TYPES.get(houseType);
        if (type == null) {
            if (houseType != null && !houseType.isBlank()) {
                throw new IllegalArgumentException("无法识别的房源类型：" + houseType);
            }
            type = "PUBLIC_RENTAL";
        }
        BigDecimal area = null;
        if (areaText != null && !areaText.isBlank()) {
            try { area = new BigDecimal(areaText); } catch (NumberFormatException e) {
                throw new IllegalArgumentException("建筑面积不是数字：" + areaText);
            }
        }
        long id = idGen.nextId();
        String code = houseCode == null || houseCode.isBlank() ? "HS" + id : houseCode.trim();
        String name = houseName == null || houseName.isBlank()
                ? String.valueOf(leaf.get("spacePath")).substring(String.valueOf(leaf.get("spacePath")).lastIndexOf('/') + 1)
                : houseName.trim();
        jdbc.update("insert into bp_house(id,tenant_id,org_id,space_id,house_code,house_name,"
                        + "asset_type_code,area,house_status,is_deleted) values(?,?,?,?,?,?,?,?, 'VACANT',0)",
                id, tenant, projectId, spaceId, code, name, type, area);
        counters[1]++;
        cache.put(spaceId, id);
        return id;
    }

    private boolean ensureDevice(String tenant, long projectId, long spaceId, String deviceCode,
                                 String type, String name, String mac) {
        long id = idGen.nextId();
        String code = deviceCode == null || deviceCode.isBlank() ? "DV" + id : deviceCode.trim();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, space_id spaceId, device_mac deviceMac from bp_dev_device "
                        + "where tenant_id=? and project_id=? and device_code=? and is_deleted=0",
                tenant, projectId, code);
        if (rows.size() > 1) throw new IllegalArgumentException("设备编号重复：" + code);
        if (rows.size() == 1) {
            Map<String, Object> row = rows.get(0);
            Object boundSpace = row.get("spaceId");
            if (boundSpace != null && ((Number) boundSpace).longValue() != spaceId) {
                throw new IllegalArgumentException("设备已绑定其他空间：" + code);
            }
            String currentMac = row.get("deviceMac") == null ? null : String.valueOf(row.get("deviceMac"));
            if (mac != null && !mac.isBlank() && !mac.equals(currentMac)) {
                requireMacFree(tenant, mac, code);
                jdbc.update("update bp_dev_device set device_mac=?, is_virtual=0, install_status='INSTALLED', "
                                + "install_time=coalesce(install_time, now()), space_id=?, update_time=now() "
                                + "where tenant_id=? and device_code=? and is_deleted=0",
                        mac, spaceId, tenant, code);
            }
            return false;
        }
        if (mac != null && !mac.isBlank()) requireMacFree(tenant, mac, code);
        boolean virtual = mac == null || mac.isBlank();
        jdbc.update("insert into bp_dev_device(id,tenant_id,project_id,space_id,device_code,device_name,"
                        + "device_type,asset_status,business_status,device_mac,is_virtual,install_status,"
                        + "install_time,is_deleted) values(?,?,?,?,?,?,?, 'ACTIVE','IN_USE',?,?,?,?,0)",
                id, tenant, projectId, spaceId, code,
                name == null || name.isBlank() ? type : name.trim(), type,
                mac == null || mac.isBlank() ? null : mac,
                virtual ? 1 : 0, virtual ? "PENDING_INSTALL" : "INSTALLED",
                virtual ? null : LocalDateTime.now());
        return true;
    }

    private void requireMacFree(String tenant, String mac, String deviceCode) {
        Long count = jdbc.queryForObject(
                "select count(*) from bp_dev_device where tenant_id=? and device_mac=? "
                        + "and device_code<>? and is_deleted=0",
                Long.class, tenant, mac, deviceCode);
        if (count != null && count > 0) {
            throw new IllegalArgumentException("物理MAC已被其他设备使用：" + mac);
        }
    }

    private static void requireParent(Map<String, Object> parent, String child, String required) {
        if (parent == null) {
            throw new IllegalArgumentException("填写" + child + "前必须填写" + required);
        }
    }

    private static String v(String[] c, int i) {
        return i < c.length ? c[i].trim() : "";
    }

    private static String[] split(String line) {
        List<String> out = new ArrayList<>();
        StringBuilder b = new StringBuilder();
        boolean quote = false;
        for (int i = 0; i < line.length(); i++) {
            char ch = line.charAt(i);
            if (ch == '"') {
                if (quote && i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    b.append('"');
                    i++;
                } else {
                    quote = !quote;
                }
            } else if (ch == ',' && !quote) {
                out.add(b.toString());
                b.setLength(0);
            } else {
                b.append(ch);
            }
        }
        out.add(b.toString());
        return out.toArray(new String[0]);
    }

    private static Map<String, Object> err(int line, String message) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("line", line);
        m.put("message", message);
        return m;
    }
}
