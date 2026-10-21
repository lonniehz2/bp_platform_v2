package com.yundao.bp.dev.service;

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
        if (pathCode == null || pathCode.isBlank() || anchor.getOrgId() == null) {
            // 没有物化路径或组织（异常数据）：只取自身，避免误伤
            return new ArrayList<>(List.of(anchor.getId()));
        }
        // ⚠️ 不用 .select(AssetSpace::getId)：LambdaQueryWrapper 的 select(SFunction)
        //    会立刻解析列名，依赖 MyBatis-Plus 的 TableInfo 缓存，
        //    在纯单测（无 MyBatis 上下文）里会 NPE。返回整实体无副作用。
        //
        // ⚠️⚠️ 必须限定同一个 org_id！
        //    path_code 是"组织内"的物化路径，各小区的顶层楼栋都从 '01/' 开始，
        //    若只按 path_code 前缀匹配，A 小区的授权会把 B 小区的设备也算进来
        //    （同租户内跨组织越权，已由实测验证过）。
        LambdaQueryWrapper<AssetSpace> qw = new LambdaQueryWrapper<AssetSpace>()
                .eq(AssetSpace::getOrgId, anchor.getOrgId())
                .likeRight(AssetSpace::getPathCode, pathCode);
        List<AssetSpace> spaces = spaceMapper.selectList(qw);
        // likeRight 已包含自身（自身的 path_code 以自身为前缀）
        Set<Long> ids = new LinkedHashSet<>();
        ids.add(anchor.getId());
        spaces.forEach(s -> ids.add(s.getId()));
        return new ArrayList<>(ids);
    }
}
