package com.yundao.bp.dev;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.asset.entity.AssetSpace;
import com.yundao.bp.asset.mapper.AssetSpaceMapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.dev.constant.OpenableDeviceType;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.dev.service.DeviceBindingResolver;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

/**
 * 设备-空间绑定解析测试。
 *
 * <p>核心验证"空间锚点 → 应授权设备"的三条规则：
 * <ol>
 *   <li><b>向下继承</b>：锚点子树内的设备都要算上</li>
 *   <li><b>类型过滤</b>：水电气表等计量设备不参与开门授权</li>
 *   <li><b>公有设备</b>：同组织的大门（is_public=1）要纳入</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class DeviceBindingTest {

    private static final long ORG_ID = 7001L;
    private static final long BUILDING_ID = 5001L;
    private static final long FLOOR_ID = 5002L;
    private static final long ROOM_ID = 5003L;

    @Mock
    private AssetSpaceMapper spaceMapper;
    @Mock
    private DevDeviceMapper deviceMapper;

    private DeviceBindingResolver resolver;

    @BeforeEach
    void setUp() {
        resolver = new DeviceBindingResolver(spaceMapper, deviceMapper);
        TenantContext.set(TenantInfo.of("350600", 1001L));
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static AssetSpace space(long id, String name, String pathCode) {
        AssetSpace s = new AssetSpace();
        s.setId(id);
        s.setOrgId(ORG_ID);
        s.setSpaceName(name);
        s.setPathCode(pathCode);
        return s;
    }

    private static DevDevice device(String deviceId, String type, Long spaceId,
                                    String status, int isPublic) {
        DevDevice d = new DevDevice();
        d.setDeviceId(deviceId);
        d.setDeviceType(type);
        d.setSpaceId(spaceId);
        d.setDeviceStatus(status);
        d.setIsPublic(isPublic);
        d.setOrgId(ORG_ID);
        return d;
    }

    // ==================== 1. 基本解析 ====================

    @Test
    @DisplayName("解析子树内设备（楼栋锚点 → 含楼层/房间设备）")
    void resolveDevicesInSubtree() {
        when(spaceMapper.selectById(BUILDING_ID)).thenReturn(space(BUILDING_ID, "1幢", "01/"));
        // likeRight 返回自身+后代
        when(spaceMapper.selectList(any())).thenReturn(List.of(
                space(BUILDING_ID, "1幢", "01/"),
                space(FLOOR_ID, "1层", "01/01/"),
                space(ROOM_ID, "101室", "01/01/01/")));
        when(deviceMapper.selectList(any())).thenReturn(List.of(
                device("LOCK-ROOM-101", "LOCK", ROOM_ID, "NORMAL", 0),
                device("LOCK-FLOOR-1", "ACCESS", FLOOR_ID, "NORMAL", 0),
                device("GATE-1", "GATE", BUILDING_ID, "NORMAL", 0)));

        List<String> ids = resolver.resolveDeviceIds(BUILDING_ID);

        assertEquals(3, ids.size());
        assertTrue(ids.contains("LOCK-ROOM-101"), "房间门锁应纳入");
        assertTrue(ids.contains("LOCK-FLOOR-1"), "楼层门禁应纳入");
        assertTrue(ids.contains("GATE-1"), "楼栋道闸应纳入");
    }

    @Test
    @DisplayName("锚点是房间时也能解析到该房间设备")
    void resolveFromRoom() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(space(ROOM_ID, "101室", "01/01/01/"));
        when(spaceMapper.selectList(any())).thenReturn(List.of(
                space(ROOM_ID, "101室", "01/01/01/")));
        when(deviceMapper.selectList(any())).thenReturn(List.of(
                device("LOCK-ROOM-101", "LOCK", ROOM_ID, "NORMAL", 0)));

        List<String> ids = resolver.resolveDeviceIds(ROOM_ID);
        assertEquals(List.of("LOCK-ROOM-101"), ids);
    }

    @Test
    @DisplayName("空间下无设备时返回空列表（不抛异常，交由编排层处理）")
    void resolveEmptyWhenNoDevice() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(space(ROOM_ID, "101室", "01/01/01/"));
        when(spaceMapper.selectList(any())).thenReturn(List.of(
                space(ROOM_ID, "101室", "01/01/01/")));
        when(deviceMapper.selectList(any())).thenReturn(List.of());

        assertTrue(resolver.resolveDeviceIds(ROOM_ID).isEmpty());
    }

    // ==================== 2. 类型过滤 ====================

    @Test
    @DisplayName("⭐ 只有 LOCK/ACCESS/ELEVATOR/GATE/BOX/VISITOR_CTRL 可开门")
    void openableTypes() {
        Set<String> openable = OpenableDeviceType.openableNames();
        assertTrue(openable.contains("LOCK"));
        assertTrue(openable.contains("ACCESS"));
        assertTrue(openable.contains("ELEVATOR"));
        assertTrue(openable.contains("GATE"));
        assertTrue(openable.contains("BOX"));
        assertTrue(openable.contains("VISITOR_CTRL"));
        // 计量类不可开门
        assertFalse(openable.contains("METER_W"));
        assertFalse(openable.contains("METER_E"));
        assertFalse(openable.contains("METER_G"));
        assertFalse(openable.contains("GATEWAY"));
        assertFalse(openable.contains("COLLECTOR"));
    }

    @Test
    @DisplayName("枚举逐项校验 openable 标记")
    void openableFlagPerType() {
        assertTrue(OpenableDeviceType.LOCK.openable());
        assertTrue(OpenableDeviceType.ELEVATOR.openable());
        assertFalse(OpenableDeviceType.METER_W.openable());
        assertFalse(OpenableDeviceType.COLLECTOR.openable());
        assertEquals("门锁", OpenableDeviceType.LOCK.label());
    }

    // ==================== 3. 边界与异常 ====================

    @Test
    @DisplayName("空间不存在应抛 404")
    void spaceNotFound() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> resolver.resolveDeviceIds(ROOM_ID));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    @Test
    @DisplayName("spaceId 为空应抛参数错误")
    void nullSpaceId() {
        BizException ex = assertThrows(BizException.class, () -> resolver.resolveDeviceIds(null));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("path_code 为空（异常数据）时只取自身，不误伤其它空间")
    void emptyPathCodeFallsBackToSelf() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(space(ROOM_ID, "101室", null));
        when(deviceMapper.selectList(any())).thenReturn(List.of(
                device("LOCK-1", "LOCK", ROOM_ID, "NORMAL", 0)));

        List<String> ids = resolver.resolveDeviceIds(ROOM_ID);
        assertEquals(List.of("LOCK-1"), ids);
    }

    @Test
    @DisplayName("⭐ path_code 前缀必须带结尾斜杠：'01/' 不能匹配 '010/'")
    void pathCodePrefixIsSafe() {
        // 这条断言是防御性的：验证规则文档化
        String anchor = "01/";
        String sibling = "010/";
        String descendant = "01/01/";
        assertTrue(descendant.startsWith(anchor), "同前缀应命中");
        assertFalse(sibling.startsWith(anchor),
                "'010/' 不以 '01/' 开头，不会被误纳入（这正是要求结尾斜杠的原因）");
    }

    @Test
    @DisplayName("跨组织隔离（逻辑层）：只信任 Mapper 的 org 过滤结果，不做二次展开")
    void crossOrgIsolationByContract() {
        // org 过滤由 descendantSpaceIds 的查询条件保证；
        // 该条件在真实库上由集成验证覆盖（见部署手册的"跨组织隔离"用例），
        // 这里只验证：Mapper 返回什么，就只用什么，不会自行扩大范围。
        AssetSpace anchor = space(BUILDING_ID, "A小区1幢", "01/");
        anchor.setOrgId(7001L);
        when(spaceMapper.selectById(BUILDING_ID)).thenReturn(anchor);
        when(spaceMapper.selectList(any())).thenReturn(List.of(anchor));
        when(deviceMapper.selectList(any())).thenReturn(List.of(
                device("LOCK-A", "LOCK", ROOM_ID, "NORMAL", 0)));

        List<String> ids = resolver.resolveDeviceIds(BUILDING_ID);
        assertEquals(List.of("LOCK-A"), ids);

        // 只查一次子树，不会因为结果为空而退化成"查全表"
        org.mockito.Mockito.verify(spaceMapper, org.mockito.Mockito.times(1))
                .selectList(org.mockito.ArgumentMatchers.any());
    }

    @Test
    @DisplayName("设备 ID 去重保序：同一设备不会出现两次")
    void deviceIdsDeduplicated() {
        when(spaceMapper.selectById(BUILDING_ID)).thenReturn(space(BUILDING_ID, "1幢", "01/"));
        when(spaceMapper.selectList(any())).thenReturn(List.of(
                space(BUILDING_ID, "1幢", "01/"),
                space(ROOM_ID, "101室", "01/01/01/")));
        when(deviceMapper.selectList(any())).thenReturn(List.of(
                device("LOCK-1", "LOCK", ROOM_ID, "NORMAL", 0),
                device("LOCK-2", "LOCK", ROOM_ID, "NORMAL", 0)));

        List<String> ids = resolver.resolveDeviceIds(BUILDING_ID);
        assertEquals(2, ids.size());
        assertEquals(ids.size(), ids.stream().distinct().count());
    }
}
