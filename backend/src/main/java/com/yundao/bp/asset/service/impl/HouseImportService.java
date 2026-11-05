package com.yundao.bp.asset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.constant.SpaceType;
import com.yundao.bp.asset.dto.HouseCreateCmd;
import com.yundao.bp.asset.dto.SpaceCreateCmd;
import com.yundao.bp.asset.dto.SpaceVO;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.entity.AssetSpace;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.mapper.AssetSpaceMapper;
import com.yundao.bp.asset.service.HouseService;
import com.yundao.bp.asset.service.SpaceService;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.dev.constant.DevDeviceType;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.iam.entity.IamOrg;
import com.yundao.bp.iam.mapper.IamOrgMapper;
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
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

/**
 * 一张长表批量导入：空间树 + 房源 + 设备 + 绑定。
 *
 * <p>一行一台设备；同一空间多行自动归并。设备编号为空生成 DV+雪花ID。
 * 设备可暂无物理 MAC，作为虚拟设备等待 IoT 安装单回填。
 */
@Service
public class HouseImportService {

    private final IamOrgMapper orgMapper;
    private final AssetSpaceMapper spaceMapper;
    private final AssetHouseMapper houseMapper;
    private final DevDeviceMapper deviceMapper;
    private final SpaceService spaceService;
    private final HouseService houseService;
    private final SnowflakeIdGenerator idGen;

    private static final Map<String, String> HOUSE_TYPES = new HashMap<>();
    private static final Map<String, String> DEVICE_TYPES = new HashMap<>();

    static {
        HOUSE_TYPES.put("PUBLIC_RENTAL", "PUBLIC_RENTAL");
        HOUSE_TYPES.put("公租房", "PUBLIC_RENTAL");
        HOUSE_TYPES.put("AFFORDABLE_RENTAL", "AFFORDABLE_RENTAL");
        HOUSE_TYPES.put("保障性租赁住房", "AFFORDABLE_RENTAL");
        HOUSE_TYPES.put("保租房", "AFFORDABLE_RENTAL");
        HOUSE_TYPES.put("TALENT", "TALENT");
        HOUSE_TYPES.put("人才公寓", "TALENT");
        HOUSE_TYPES.put("APARTMENT", "APARTMENT");
        HOUSE_TYPES.put("公寓", "APARTMENT");
        HOUSE_TYPES.put("DORMITORY", "DORMITORY");
        HOUSE_TYPES.put("宿舍", "DORMITORY");
        HOUSE_TYPES.put("RENTAL", "RENTAL");
        HOUSE_TYPES.put("出租房", "RENTAL");
        HOUSE_TYPES.put("HOTEL", "HOTEL");
        HOUSE_TYPES.put("酒店民宿", "HOTEL");
        HOUSE_TYPES.put("酒店/民宿", "HOTEL");
        for (DevDeviceType t : DevDeviceType.values()) {
            DEVICE_TYPES.put(t.name(), t.name());
            DEVICE_TYPES.put(t.label(), t.name());
        }
        DEVICE_TYPES.put("车锁", "CAR_LOCK");
        DEVICE_TYPES.put("控制主机", "CONTROLLER");
    }

    public HouseImportService(IamOrgMapper orgMapper, AssetSpaceMapper spaceMapper,
                              AssetHouseMapper houseMapper, DevDeviceMapper deviceMapper,
                              SpaceService spaceService, HouseService houseService,
                              SnowflakeIdGenerator idGen) {
        this.orgMapper = orgMapper;
        this.spaceMapper = spaceMapper;
        this.houseMapper = houseMapper;
        this.deviceMapper = deviceMapper;
        this.spaceService = spaceService;
        this.houseService = houseService;
        this.idGen = idGen;
    }

    public Map<String, Object> importCsv(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw BizException.paramInvalid("请上传 CSV 文件");
        }
        List<Map<String, Object>> errors = new ArrayList<>();
        int total = 0, devices = 0, bound = 0;
        int[] counters = new int[2]; // 0=spaces, 1=houses
        Map<String, IamOrg> orgByCode = new HashMap<>();
        for (IamOrg o : orgMapper.selectList(new LambdaQueryWrapper<>())) {
            if (o.getOrgCode() != null) {
                orgByCode.put(o.getOrgCode(), o);
            }
        }
        Map<String, Long> spaceCache = new HashMap<>();
        Map<Long, Long> houseBySpace = new HashMap<>();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(
                file.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            int lineNo = 0;
            while ((line = br.readLine()) != null) {
                lineNo++;
                line = line.replace("\ufeff", "");
                if (line.isBlank() || line.startsWith("#")) {
                    continue;
                }
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
                String deviceId = v(c, 10);
                String deviceType = v(c, 11);
                String deviceName = v(c, 12);
                String mac = v(c, 13);
                try {
                    IamOrg org = orgByCode.get(orgCode);
                    if (org == null) {
                        throw new IllegalArgumentException("组织编码不存在：" + orgCode);
                    }
                    Long parentId = null;
                    AssetSpace parent = null;
                    if (!building.isBlank()) {
                        parent = ensureSpace(org, null, "BUILDING", building, spaceCache, counters);
                        parentId = parent.getId();
                    }
                    if (!unit.isBlank()) {
                        requireParent(parent, "单元", building);
                        parent = ensureSpace(org, parentId, "UNIT", unit, spaceCache, counters);
                        parentId = parent.getId();
                    }
                    if (!floor.isBlank()) {
                        requireParent(parent, "楼层", unit);
                        parent = ensureSpace(org, parentId, "FLOOR", floor, spaceCache, counters);
                        parentId = parent.getId();
                    }
                    if (!room.isBlank()) {
                        requireParent(parent, "房间", floor);
                        parent = ensureSpace(org, parentId, "ROOM", room, spaceCache, counters);
                        parentId = parent.getId();
                    }
                    if (!bed.isBlank()) {
                        requireParent(parent, "床位/内房", room);
                        parent = ensureSpace(org, parentId, "BED", bed, spaceCache, counters);
                        parentId = parent.getId();
                    }
                    Long houseId = null;
                    if (!room.isBlank() && parent != null) {
                        houseId = ensureHouse(org, parent, houseCode, houseName, houseType, areaText,
                                houseBySpace, counters);
                    }
                    if (!deviceType.isBlank() || !deviceId.isBlank() || !mac.isBlank()) {
                        if (parent == null) {
                            throw new IllegalArgumentException("设备行必须填写空间节点");
                        }
                        String type = DEVICE_TYPES.get(deviceType);
                        if (type == null) {
                            throw new IllegalArgumentException("无法识别的设备类型：" + deviceType);
                        }
                        ensureDevice(org, parent, houseId, deviceId, type, deviceName, mac);
                        devices++;
                        bound++;
                    }
                } catch (Exception e) {
                    errors.add(err(lineNo, e.getMessage() == null ? "导入失败" : e.getMessage()));
                }
            }
        } catch (Exception e) {
            throw BizException.paramInvalid("CSV 读取失败：" + e.getMessage());
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("total", total);
        out.put("spacesCreated", counters[0]);
        out.put("housesCreated", counters[1]);
        out.put("devicesCreated", devices);
        out.put("devicesBound", bound);
        out.put("failed", errors.size());
        out.put("errors", errors);
        return out;
    }

    private AssetSpace ensureSpace(IamOrg org, Long parentId, String type, String name,
                                   Map<String, Long> cache, int[] counters) {
        String key = org.getOrgCode() + "|" + (parentId == null ? "root" : parentId) + "|" + type + "|" + name;
        Long cached = cache.get(key);
        if (cached != null) {
            return spaceMapper.selectById(cached);
        }
        LambdaQueryWrapper<AssetSpace> qw = new LambdaQueryWrapper<AssetSpace>()
                .eq(AssetSpace::getOrgId, org.getId())
                .eq(AssetSpace::getSpaceType, type)
                .eq(AssetSpace::getSpaceName, name);
        if (parentId == null) {
            qw.isNull(AssetSpace::getParentId);
        } else {
            qw.eq(AssetSpace::getParentId, parentId);
        }
        List<AssetSpace> exists = spaceMapper.selectList(qw);
        if (exists.size() > 1) {
            throw new IllegalArgumentException("空间节点重名，无法唯一确定：" + name);
        }
        AssetSpace sp;
        if (exists.size() == 1) {
            sp = exists.get(0);
        } else {
            SpaceVO vo = spaceService.create(new SpaceCreateCmd(org.getId(), parentId,
                    "SP" + idGen.nextId(), name, type, null, null, null));
            sp = spaceMapper.selectById(vo.id());
            counters[0]++;
        }
        cache.put(key, sp.getId());
        return sp;
    }

    private Long ensureHouse(IamOrg org, AssetSpace leaf, String houseCode, String houseName,
                             String houseType, String areaText,
                             Map<Long, Long> cache, int[] counters) {
        Long cached = cache.get(leaf.getId());
        if (cached != null) {
            return cached;
        }
        List<AssetHouse> exists = houseMapper.selectList(
                new LambdaQueryWrapper<AssetHouse>().eq(AssetHouse::getSpaceId, leaf.getId()));
        if (exists.size() > 1) {
            throw new IllegalArgumentException("该空间已关联多个房源，请先清理：" + leaf.getSpaceName());
        }
        if (exists.size() == 1) {
            cache.put(leaf.getId(), exists.get(0).getId());
            return exists.get(0).getId();
        }
        String type = HOUSE_TYPES.get(houseType);
        if (type == null) {
            throw new IllegalArgumentException("无法识别的房源类型：" + houseType);
        }
        String name = houseName.isBlank() ? leaf.getSpaceName() : houseName;
        BigDecimal area = null;
        if (!areaText.isBlank()) {
            area = new BigDecimal(areaText);
        }
        var vo = houseService.create(new HouseCreateCmd(leaf.getId(),
                houseCode.isBlank() ? null : houseCode, name, type,
                null, null, null, null, null, area, null, null, null, null, null,
                null, null, null, null, null, null, null, null));
        cache.put(leaf.getId(), vo.id());
        counters[1]++;
        return vo.id();
    }

    private void ensureDevice(IamOrg org, AssetSpace space, Long houseId, String deviceId,
                              String type, String name, String mac) {
        String id = deviceId.isBlank() ? "DV" + idGen.nextId() : deviceId.trim();
        DevDevice sameId = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getDeviceId, id).last("LIMIT 1"));
        if (sameId != null) {
            if (sameId.getSpaceId() != null && !sameId.getSpaceId().equals(space.getId())) {
                throw new IllegalArgumentException("设备已绑定其他空间：" + id);
            }
            if (!mac.isBlank() && !mac.equals(sameId.getDeviceMac())) {
                if (macExists(mac, id)) {
                    throw new IllegalArgumentException("物理MAC已被其他设备使用：" + mac);
                }
                sameId.setDeviceMac(mac);
                sameId.setIsVirtual(0);
                sameId.setInstallStatus("INSTALLED");
                sameId.setMacUpdatedTime(LocalDateTime.now());
                sameId.setUpdateTime(LocalDateTime.now());
                deviceMapper.updateById(sameId);
            }
            return;
        }
        if (!mac.isBlank() && macExists(mac, null)) {
            throw new IllegalArgumentException("物理MAC已被其他设备使用：" + mac);
        }
        DevDevice d = new DevDevice();
        d.setId(idGen.nextId());
        d.setTenantId(TenantContext.tenantId());
        d.setDeviceId(id);
        d.setDeviceName(name.isBlank() ? type : name);
        d.setDeviceType(type);
        d.setOrgId(org.getId());
        d.setSpaceId(space.getId());
        d.setDeviceMac(mac.isBlank() ? null : mac);
        d.setIsVirtual(mac.isBlank() ? 1 : 0);
        d.setInstallStatus(mac.isBlank() ? "PENDING_INSTALL" : "INSTALLED");
        d.setInstallTime(mac.isBlank() ? null : LocalDateTime.now());
        d.setOnlineStatus(0);
        d.setDeviceStatus("NORMAL");
        d.setIsPublic(0);
        d.setIsDeleted(0);
        d.setCreateTime(LocalDateTime.now());
        d.setUpdateTime(LocalDateTime.now());
        deviceMapper.insert(d);
    }

    private boolean macExists(String mac, String excludeId) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getDeviceMac, mac);
        if (excludeId != null) {
            qw.ne(DevDevice::getDeviceId, excludeId);
        }
        Long n = deviceMapper.selectCount(qw);
        return n != null && n > 0;
    }

    private static void requireParent(AssetSpace parent, String child, String required) {
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
                quote = !quote;
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
