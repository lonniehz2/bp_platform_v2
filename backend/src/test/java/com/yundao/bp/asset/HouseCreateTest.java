package com.yundao.bp.asset;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.asset.dto.HouseCreateCmd;
import com.yundao.bp.asset.dto.HouseVO;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.entity.AssetSpace;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.mapper.AssetSpaceMapper;
import com.yundao.bp.asset.service.HouseService;
import com.yundao.bp.asset.service.impl.HouseServiceImpl;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import java.math.BigDecimal;
import java.time.LocalDateTime;
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
 * 房源创建测试。
 *
 * <p>核心保护点：
 * <ol>
 *   <li><b>挂载节点必须是 ROOM / BED</b> —— 防止房源挂到楼栋/单元上</li>
 *   <li><b>orgId 从空间节点派生</b>，不采信前端</li>
 *   <li>同组织内编码唯一</li>
 *   <li>初始状态 PENDING_ALLOC、入住人数 0</li>
 * </ol>
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class HouseCreateTest {

    private static final long ORG_ID = 900000L;
    private static final long ROOM_ID = 800001L;
    private static final long BUILDING_ID = 800002L;
    private static final long BED_ID = 800003L;

    @Mock
    private AssetHouseMapper houseMapper;
    @Mock
    private AssetSpaceMapper spaceMapper;

    private HouseService houseService;

    @BeforeEach
    void setUp() {
        houseService = new HouseServiceImpl(houseMapper, spaceMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(houseMapper.insert(any(AssetHouse.class))).thenReturn(1);
        when(houseMapper.updateById(any(AssetHouse.class))).thenReturn(1);
        when(houseMapper.selectCount(any())).thenReturn(0L);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static AssetSpace space(long id, String type, String name) {
        AssetSpace s = new AssetSpace();
        s.setId(id);
        s.setOrgId(ORG_ID);
        s.setSpaceType(type);
        s.setSpaceName(name);
        s.setArea(new BigDecimal("89.50"));
        return s;
    }

    private static HouseCreateCmd cmd(Long spaceId, String code) {
        return new HouseCreateCmd(spaceId, code, "101室房源", "PUBLIC_RENTAL",
                "HIGH", "CIVIL", "2居", 10, "南",
                new BigDecimal("89.50"), null, "FINE", "PUBLIC",
                new BigDecimal("12.50"), "AREA_MONTH", "INDEPENDENT", 3, "SELF", "STATE",
                null, null, null, "测试房源");
    }

    // ==================== 成功路径 ====================

    @Test
    @DisplayName("挂到 ROOM 节点创建成功")
    void createOnRoom() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(space(ROOM_ID, "ROOM", "101室"));

        HouseVO vo = houseService.create(cmd(ROOM_ID, "H-001"));

        assertEquals("H-001", vo.houseCode());
        assertEquals("101室房源", vo.houseName());
        assertEquals("PUBLIC_RENTAL", vo.houseType());
        assertEquals(ROOM_ID, vo.spaceId());
        assertEquals("PENDING_ALLOC", vo.houseStatus());
        assertEquals("待分配", vo.houseStatusLabel());
        assertEquals(0, vo.currentCapacity(), "初始已入住人数必须为 0");
        assertEquals(new BigDecimal("89.50"), vo.area());
        assertNotNull(vo.id());
    }

    @Test
    @DisplayName("挂到 BED 节点也允许（床位级房源）")
    void createOnBed() {
        when(spaceMapper.selectById(BED_ID)).thenReturn(space(BED_ID, "BED", "101-A床"));
        HouseVO vo = houseService.create(cmd(BED_ID, "H-BED-001"));
        assertEquals(BED_ID, vo.spaceId());
        assertEquals("PENDING_ALLOC", vo.houseStatus());
    }

    @Test
    @DisplayName("⭐ orgId 从空间节点派生，不采信前端")
    void orgIdDerivedFromSpace() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(space(ROOM_ID, "ROOM", "101室"));
        HouseVO vo = houseService.create(cmd(ROOM_ID, "H-002"));
        assertEquals(ORG_ID, vo.orgId(), "orgId 必须来自空间节点，不能被请求参数覆盖");
    }

    @Test
    @DisplayName("未传面积时继承空间节点面积")
    void areaInheritedFromSpace() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(space(ROOM_ID, "ROOM", "101室"));
        HouseCreateCmd c = new HouseCreateCmd(ROOM_ID, "H-003", "继承面积", "TALENT",
                null, null, null, null, null, null, null, null, null, null, null, null,
                2, null, null, null, null, null, null);
        HouseVO vo = houseService.create(c);
        assertEquals(new BigDecimal("89.50"), vo.area());
    }

    @Test
    @DisplayName("新建房源 vacantDays = 0（刚进入待分配）")
    void vacantDaysZeroOnCreate() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(space(ROOM_ID, "ROOM", "101室"));
        HouseVO vo = houseService.create(cmd(ROOM_ID, "H-004"));
        assertEquals(0L, vo.vacantDays());
    }

    // ==================== 挂载节点校验 ====================

    @Test
    @DisplayName("⭐ 挂到 BUILDING 节点应被拒（BP10001）")
    void rejectOnBuilding() {
        when(spaceMapper.selectById(BUILDING_ID)).thenReturn(space(BUILDING_ID, "BUILDING", "1幢"));

        BizException ex = assertThrows(BizException.class,
                () -> houseService.create(cmd(BUILDING_ID, "H-BAD")));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("ROOM 或 BED"), ex.getMessage());
        assertTrue(ex.getMessage().contains("1幢"), "错误信息应指出具体节点");
    }

    @Test
    @DisplayName("挂到 UNIT / FLOOR / PARKING 也应被拒")
    void rejectOnOtherTypes() {
        for (String type : new String[]{"UNIT", "FLOOR", "PARKING", "AREA"}) {
            when(spaceMapper.selectById(BUILDING_ID)).thenReturn(space(BUILDING_ID, type, "某节点"));
            BizException ex = assertThrows(BizException.class,
                    () -> houseService.create(cmd(BUILDING_ID, "H-BAD-" + type)),
                    "类型 " + type + " 不应允许挂房源");
            assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        }
    }

    @Test
    @DisplayName("空间节点不存在应报 404（BP30001）")
    void rejectMissingSpace() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> houseService.create(cmd(ROOM_ID, "H-005")));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    // ==================== 唯一性与租户 ====================

    @Test
    @DisplayName("同组织内房源编号重复应被拒（BP30002）")
    void rejectDuplicateCode() {
        when(spaceMapper.selectById(ROOM_ID)).thenReturn(space(ROOM_ID, "ROOM", "101室"));
        when(houseMapper.selectCount(any())).thenReturn(1L);

        BizException ex = assertThrows(BizException.class,
                () -> houseService.create(cmd(ROOM_ID, "H-DUP")));
        assertEquals(ErrorCode.DUPLICATED, ex.errorCode());
        assertTrue(ex.getMessage().contains("H-DUP"));
    }

    @Test
    @DisplayName("无租户上下文时拒绝创建")
    void rejectNoTenant() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class,
                () -> houseService.create(cmd(ROOM_ID, "H-006")));
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
    }

    // ==================== 状态机 ====================

    @Test
    @DisplayName("状态迁移 PENDING_ALLOC → LOCKED 合法")
    void statusTransitionValid() {
        AssetHouse e = new AssetHouse();
        e.setId(1L);
        e.setOrgId(ORG_ID);
        e.setHouseCode("H-100");
        e.setHouseStatus("PENDING_ALLOC");
        e.setLockStatusTime(LocalDateTime.now());
        when(houseMapper.selectById(1L)).thenReturn(e);

        HouseVO vo = houseService.changeStatus(1L, "LOCKED");
        assertEquals("LOCKED", vo.houseStatus());
    }

    @Test
    @DisplayName("非法状态值应被拒（BP10001）")
    void statusInvalid() {
        BizException ex = assertThrows(BizException.class,
                () -> houseService.changeStatus(1L, "WHATEVER"));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("非空置状态 vacantDays 为 null（表示不适用，而非 0）")
    void vacantDaysNullForNonPoolable() {
        AssetHouse e = new AssetHouse();
        e.setId(1L);
        e.setOrgId(ORG_ID);
        e.setHouseStatus("OCCUPIED");
        e.setLockStatusTime(LocalDateTime.now().minusDays(30));
        when(houseMapper.selectById(1L)).thenReturn(e);

        HouseVO vo = houseService.get(1L);
        assertNull(vo.vacantDays(), "已入住不应有空置天数");
    }

    @Test
    @DisplayName("空置状态 vacantDays 按状态变更时间计算")
    void vacantDaysComputed() {
        AssetHouse e = new AssetHouse();
        e.setId(1L);
        e.setOrgId(ORG_ID);
        e.setHouseStatus("VACANT");
        e.setLockStatusTime(LocalDateTime.now().minusDays(7));
        when(houseMapper.selectById(1L)).thenReturn(e);

        HouseVO vo = houseService.get(1L);
        assertEquals(7L, vo.vacantDays());
    }
}
