# -*- coding: utf-8 -*-
"""设备-空间绑定解析（dev 包）+ 接入 grant"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['dev/constant/OpenableDeviceType.java'] = '''package com.yundao.bp.dev.constant;

import java.util.Arrays;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 设备类型（对应 {@code bp_dev_device.device_type}）。
 *
 * <p>只有"可开门"类型才参与授权下发；水电气表等计量设备不参与。
 */
public enum OpenableDeviceType {

    LOCK("门锁", true),
    ACCESS("门禁", true),
    ELEVATOR("梯控", true),
    GATE("道闸", true),
    METER_W("水表", false),
    METER_E("电表", false),
    METER_G("燃气表", false),
    GATEWAY("网关", false),
    COLLECTOR("采集器", false),
    BOX("车闸盒子", true),
    VISITOR_CTRL("访客码控制器", true);

    private final String label;
    private final boolean openable;

    OpenableDeviceType(String label, boolean openable) {
        this.label = label;
        this.openable = openable;
    }

    public String label() {
        return label;
    }

    /** 是否可参与开门授权。 */
    public boolean openable() {
        return openable;
    }

    /** 所有可开门类型的名字集合（用于 SQL IN 过滤）。 */
    public static Set<String> openableNames() {
        return Arrays.stream(values()).filter(OpenableDeviceType::openable)
                .map(Enum::name).collect(Collectors.toSet());
    }
}
'''

FILES['dev/entity/DevDevice.java'] = '''package com.yundao.bp.dev.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 设备台账。对应 {@code bp_dev_device}。
 *
 * <p>⭐ <b>设备-空间绑定关系就靠 {@code spaceId}</b>（安装空间），
 * 层级继承通过空间树的 {@code path_code} 前缀实现，无需额外绑定表。
 */
@Data
@TableName("bp_dev_device")
public class DevDevice {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;

    /** IoT 平台侧设备标识（门锁即 lockId） */
    private String deviceId;
    private String deviceMac;
    private String deviceName;

    /** LOCK / ACCESS / ELEVATOR / GATE / METER_* / ... 见 OpenableDeviceType */
    private String deviceType;
    private String deviceModel;
    private String lockType;
    private String ventor;

    private Long orgId;
    /** 安装空间（绑定锚点） */
    private Long spaceId;
    private String installAddress;
    private LocalDateTime installTime;

    private Integer onlineStatus;
    private LocalDateTime onlineTime;
    private LocalDateTime offlineTime;
    private Integer battery;
    private String rssi;

    /** 是否公有设备（小区大门等，通常对所有住户开放） */
    private Integer isPublic;

    private Long ownerPersonId;
    private Long adminPersonId;
    private Long usablePersonId;
    private String agentCode;

    /** NORMAL / MAINTENANCE / SCRAPPED / UNKNOWN */
    private String deviceStatus;
    private String remark;

    @TableLogic
    private Integer isDeleted;

    private String createBy;
    private LocalDateTime createTime;
    private String updateBy;
    private LocalDateTime updateTime;
}
'''

FILES['dev/mapper/DevDeviceMapper.java'] = '''package com.yundao.bp.dev.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.dev.entity.DevDevice;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DevDeviceMapper extends BaseMapper<DevDevice> {
}
'''

FILES['dev/service/DeviceBindingResolver.java'] = '''package com.yundao.bp.dev.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.entity.AssetSpace;
import com.yundao.bp.asset.mapper.AssetSpaceMapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.dev.constant.OpenableDeviceType;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * 设备-空间绑定解析：给定一个空间锚点，算出"应该被授权的设备"。
 *
 * <p><b>规则</b>（设计决策 R3：权限锚点向下继承）：
 * <ol>
 *   <li><b>向下继承</b>：锚点空间 + 其所有后代空间下的设备。
 *       利用空间树的 {@code path_code} 前缀匹配（每级 2 位且带结尾 {@code /}，
 *       因此 {@code LIKE '01/01/%'} 不会误匹配 {@code '01/010/'}）。</li>
 *   <li><b>类型过滤</b>：仅 {@link OpenableDeviceType#openable()} 为真的设备
 *       （门锁/门禁/梯控/道闸），水电气表不参与开门授权。</li>
 *   <li><b>状态过滤</b>：排除已报废（{@code SCRAPPED}）。维护中仍下发
 *       （设备恢复后权限即生效），但会在日志中标注。</li>
 *   <li><b>公有设备</b>：同组织下的 {@code is_public=1} 设备（小区大门等）一并纳入，
 *       否则住户无法开大门。</li>
 * </ol>
 *
 * <p><b>为什么不用绑定表</b>：{@code bp_dev_device.space_id} 已经是直接绑定，
 * 加上空间树的物化路径，一次前缀查询即可覆盖整棵子树，比多一张关系表更简单且不易失配。
 */
@Service
public class DeviceBindingResolver {

    private static final Logger log = LoggerFactory.getLogger(DeviceBindingResolver.class);

    private final AssetSpaceMapper spaceMapper;
    private final DevDeviceMapper deviceMapper;

    public DeviceBindingResolver(AssetSpaceMapper spaceMapper, DevDeviceMapper deviceMapper) {
        this.spaceMapper = spaceMapper;
        this.deviceMapper = deviceMapper;
    }

    /**
     * 解析锚点空间下应被授权的设备 ID 列表（去重，保持顺序）。
     *
     * @param spaceId 权限锚点空间
     * @return IoT 侧 device_id 列表（可能为空）
     * @throws BizException 空间不存在时
     */
    public List<String> resolveDeviceIds(Long spaceId) {
        return resolveDevices(spaceId).stream().map(DevDevice::getDeviceId).toList();
    }

    /** 解析锚点空间下的设备实体列表。 */
    public List<DevDevice> resolveDevices(Long spaceId) {
        if (spaceId == null) {
            throw BizException.paramInvalid("授权空间不能为空");
        }
        AssetSpace anchor = spaceMapper.selectById(spaceId);
        if (anchor == null) {
            throw BizException.notFound("空间节点");
        }

        List<Long> spaceIds = descendantSpaceIds(anchor);
        if (spaceIds.isEmpty()) {
            return Collections.emptyList();
        }

        Set<String> openable = OpenableDeviceType.openableNames();
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<DevDevice>()
                .in(DevDevice::getDeviceType, openable)
                .ne(DevDevice::getDeviceStatus, "SCRAPPED")
                // 子树内设备
                .and(w -> {
                    w.in(DevDevice::getSpaceId, spaceIds);
                    // 公有设备（小区大门等）按组织纳入
                    if (anchor.getOrgId() != null) {
                        w.or(x -> x.eq(DevDevice::getIsPublic, 1)
                                .eq(DevDevice::getOrgId, anchor.getOrgId()));
                    }
                })
                .orderByAsc(DevDevice::getId);

        List<DevDevice> devices = deviceMapper.selectList(qw);
        if (devices.isEmpty()) {
            log.warn("空间 {}（path_code={}）下没有可开门设备",
                    anchor.getSpaceName(), anchor.getPathCode());
        } else {
            long maintenance = devices.stream()
                    .filter(d -> "MAINTENANCE".equals(d.getDeviceStatus())).count();
            if (maintenance > 0) {
                log.info("空间 {} 下有 {} 台设备处于维护中，仍下发授权", anchor.getSpaceName(), maintenance);
            }
        }
        return devices;
    }

    /**
     * 锚点空间自身 + 全部后代空间的 ID。
     *
     * <p>用 {@code path_code} 前缀匹配。<b>必须带结尾 {@code /}</b>：
     * 若只匹配 {@code '01'}，会把 {@code '010/'} 这类兄弟节点误纳进来。
     */
    private List<Long> descendantSpaceIds(AssetSpace anchor) {
        String pathCode = anchor.getPathCode();
        if (pathCode == null || pathCode.isBlank()) {
            // 没有物化路径（异常数据）：只取自身
            return new ArrayList<>(List.of(anchor.getId()));
        }
        List<AssetSpace> spaces = spaceMapper.selectList(new LambdaQueryWrapper<AssetSpace>()
                .select(AssetSpace::getId)
                .likeRight(AssetSpace::getPathCode, pathCode));
        // likeRight 已包含自身（自身的 path_code 以自身为前缀）
        Set<Long> ids = new LinkedHashSet<>();
        ids.add(anchor.getId());
        spaces.forEach(s -> ids.add(s.getId()));
        return new ArrayList<>(ids);
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('\n共 %d 个文件' % count)
