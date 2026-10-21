package com.yundao.bp.asset;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.asset.constant.HouseStatus;
import com.yundao.bp.asset.constant.SpaceType;
import com.yundao.bp.asset.dto.HouseVO;
import com.yundao.bp.asset.dto.SpaceCreateCmd;
import com.yundao.bp.asset.dto.SpaceVO;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.entity.AssetSpace;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.mapper.AssetSpaceMapper;
import com.yundao.bp.asset.service.HouseService;
import com.yundao.bp.asset.service.SpaceService;
import com.yundao.bp.asset.service.impl.HouseServiceImpl;
import com.yundao.bp.asset.service.impl.SpaceServiceImpl;
import com.yundao.bp.asset.util.PathCodeUtil;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import java.time.LocalDateTime;
import java.util.Set;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

/**
 * asset 模块测试：空间层级、编码规则、房源状态机。
 */
@ExtendWith(MockitoExtension.class)
class AssetModuleTest {

    @Mock
    private AssetSpaceMapper spaceMapper;
    @Mock
    private AssetHouseMapper houseMapper;

    private SpaceService spaceService;
    private HouseService houseService;

    @BeforeEach
    void setUp() {
        SnowflakeIdGenerator gen = new SnowflakeIdGenerator(1, 1);
        spaceService = new SpaceServiceImpl(spaceMapper, houseMapper, gen);
        houseService = new HouseServiceImpl(houseMapper, spaceMapper, gen);
        TenantContext.set(TenantInfo.of("350600", 1001L));
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    // ==================== path_code 规则 ====================

    @Test
    @DisplayName("path_code：每级 2 位且以 / 结尾")
    void pathCodeFormat() {
        assertEquals("01/", PathCodeUtil.build(null, 1));
        assertEquals("01/01/", PathCodeUtil.build("01/", 1));
        assertEquals("01/01/02/", PathCodeUtil.build("01/01/", 2));
        assertEquals("01/01/02/05/", PathCodeUtil.build("01/01/02/", 5));
    }

    @Test
    @DisplayName("path_code：前缀 LIKE 不会误匹配（结尾 / 的作用）")
    void pathCodeNoFalsePrefixMatch() {
        String p = PathCodeUtil.build(null, 1);          // "01/"
        String pattern = PathCodeUtil.prefixPattern(p);  // "01/%"
        assertEquals("01/%", pattern);
        // "011/" 不会被 "01/%" 匹配
        assertFalse("011/".startsWith("01/"));
        assertTrue("01/02/".startsWith("01/"));
    }

    @Test
    @DisplayName("path_code：序号越界应拒绝")
    void pathCodeSeqRange() {
        assertThrows(IllegalArgumentException.class, () -> PathCodeUtil.build(null, 0));
        assertThrows(IllegalArgumentException.class, () -> PathCodeUtil.build(null, 100));
    }

    @Test
    @DisplayName("path_code 深度解析")
    void pathCodeDepth() {
        assertEquals(1, PathCodeUtil.depth("01/"));
        assertEquals(3, PathCodeUtil.depth("01/01/02/"));
        assertEquals(0, PathCodeUtil.depth(""));
    }

    @Test
    @DisplayName("space_path：祖先 ID 链")
    void spacePathChain() {
        assertEquals("", PathCodeUtil.buildSpacePath(null, null));
        assertEquals("900001/", PathCodeUtil.buildSpacePath(null, 900001L));
        assertEquals("900001/900002/", PathCodeUtil.buildSpacePath("900001/", 900002L));
    }

    // ==================== 空间层级 ====================

    @Test
    @DisplayName("层级链：楼栋→单元→楼层→房间→床位")
    void spaceTypeChain() {
        assertEquals(SpaceType.UNIT, SpaceType.nextOf(SpaceType.BUILDING));
        assertEquals(SpaceType.FLOOR, SpaceType.nextOf(SpaceType.UNIT));
        assertEquals(SpaceType.ROOM, SpaceType.nextOf(SpaceType.FLOOR));
        assertEquals(SpaceType.BED, SpaceType.nextOf(SpaceType.ROOM));
        assertEquals(null, SpaceType.nextOf(SpaceType.BED), "床位是叶子节点");
    }

    @Test
    @DisplayName("只有 ROOM / BED 可挂房源")
    void onlyRoomOrBedHostHouse() {
        assertTrue(SpaceType.ROOM.canHostHouse());
        assertTrue(SpaceType.BED.canHostHouse());
        assertFalse(SpaceType.BUILDING.canHostHouse());
        assertFalse(SpaceType.FLOOR.canHostHouse());
        assertFalse(SpaceType.PARKING.canHostHouse());
    }

    @Test
    @DisplayName("创建楼栋（顶级）：level=2，path_code=01/")
    void createBuilding() {
        when(spaceMapper.selectCount(any())).thenReturn(0L);

        SpaceVO vo = spaceService.create(new SpaceCreateCmd(
                900000L, null, "B-01", "1幢", "BUILDING", null, 1, null));

        assertEquals("BUILDING", vo.spaceType());
        assertEquals(2, vo.spaceLevel());
        assertEquals("01/", vo.pathCode());
        assertEquals("", vo.spacePath());
        assertEquals("1幢", vo.fullName());
    }

    @Test
    @DisplayName("创建房间（父=楼层）：level 递增，full_name 拼接")
    void createRoomUnderFloor() {
        AssetSpace floor = new AssetSpace();
        floor.setId(900002L);
        floor.setSpaceType("FLOOR");
        floor.setSpaceLevel(4);
        floor.setSpacePath("900000/900001/");
        floor.setPathCode("01/01/01/");
        floor.setSpaceName("1层");
        floor.setFullName("1幢1单元1层");

        when(spaceMapper.selectCount(any())).thenReturn(0L);
        when(spaceMapper.selectById(900002L)).thenReturn(floor);
        when(spaceMapper.insert(any(AssetSpace.class))).thenReturn(1);

        SpaceVO vo = spaceService.create(new SpaceCreateCmd(
                900000L, 900002L, "R-101", "101室", "ROOM", null, 1, null));

        assertEquals(5, vo.spaceLevel());
        assertEquals("900000/900001/900002/", vo.spacePath());
        assertEquals("01/01/01/01/", vo.pathCode());
        assertEquals("1幢1单元1层101室", vo.fullName());
    }

    @Test
    @DisplayName("⭐ 层级约束：楼栋下不能直接建房间")
    void cannotCreateRoomUnderBuilding() {
        AssetSpace building = new AssetSpace();
        building.setId(900001L);
        building.setSpaceType("BUILDING");
        building.setSpaceLevel(2);

        when(spaceMapper.selectCount(any())).thenReturn(0L);
        when(spaceMapper.selectById(900001L)).thenReturn(building);

        BizException ex = assertThrows(BizException.class, () ->
                spaceService.create(new SpaceCreateCmd(
                        900000L, 900001L, "R-101", "101室", "ROOM", null, 1, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("单元"), "应提示楼栋下只能是单元");
    }

    @Test
    @DisplayName("⭐ 层级约束：床位下不能建子节点")
    void cannotCreateUnderBed() {
        AssetSpace bed = new AssetSpace();
        bed.setId(900003L);
        bed.setSpaceType("BED");
        bed.setSpaceLevel(6);

        when(spaceMapper.selectCount(any())).thenReturn(0L);
        when(spaceMapper.selectById(900003L)).thenReturn(bed);

        BizException ex = assertThrows(BizException.class, () ->
                spaceService.create(new SpaceCreateCmd(
                        900000L, 900003L, "X", "X", "ROOM", null, 1, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 层级约束：无父节点时只能是楼栋/片区（禁止孤立房间）")
    void topLevelMustBeBuildingOrArea() {
        BizException ex = assertThrows(BizException.class, () ->
                spaceService.create(new SpaceCreateCmd(
                        900000L, null, "R", "孤立房间", "ROOM", null, 1, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("空间编码重复应拒绝")
    void duplicateSpaceCode() {
        when(spaceMapper.selectCount(any())).thenReturn(1L);
        BizException ex = assertThrows(BizException.class, () ->
                spaceService.create(new SpaceCreateCmd(
                        900000L, null, "B-01", "1幢", "BUILDING", null, 1, null)));
        assertEquals(ErrorCode.DUPLICATED, ex.errorCode());
    }

    @Test
    @DisplayName("有子节点时不允许删除")
    void deleteWithChildrenRejected() {
        when(spaceMapper.selectCount(any())).thenReturn(1L);
        BizException ex = assertThrows(BizException.class, () -> spaceService.delete(900001L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("有房源时不允许删除")
    void deleteWithHousesRejected() {
        when(spaceMapper.selectCount(any())).thenReturn(0L);
        when(houseMapper.selectCount(any())).thenReturn(3L);
        BizException ex = assertThrows(BizException.class, () -> spaceService.delete(900001L));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("房源"));
    }

    // ==================== 房源状态机 ====================

    @Test
    @DisplayName("状态机：合法迁移通过")
    void houseStatusValidTransition() {
        AssetHouse h = new AssetHouse();
        h.setId(1L);
        h.setHouseStatus("VACANT");
        when(houseMapper.selectById(1L)).thenReturn(h);
        when(houseMapper.updateById(any(AssetHouse.class))).thenReturn(1);

        HouseVO vo = houseService.changeStatus(1L, "LOCKED");
        assertEquals("LOCKED", vo.houseStatus());
        assertEquals("锁定中", vo.houseStatusLabel());
    }

    @Test
    @DisplayName("状态机：非法迁移被拒绝")
    void houseStatusInvalidTransition() {
        AssetHouse h = new AssetHouse();
        h.setId(1L);
        h.setHouseStatus("DISABLED");
        when(houseMapper.selectById(1L)).thenReturn(h);

        // DISABLED 只能 -> VACANT / PENDING_ALLOC，不能直接 -> OCCUPIED
        BizException ex = assertThrows(BizException.class,
                () -> houseService.changeStatus(1L, "OCCUPIED"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("状态机：所有状态都有明确的迁移目标集合")
    void houseStatusAllDefined() {
        for (HouseStatus s : HouseStatus.values()) {
            Set<HouseStatus> next = HouseStatus.nextOf(s);
            assertFalse(next.isEmpty(), s + " 没有可达状态，状态机不完整");
        }
    }

    @Test
    @DisplayName("可配租池状态正确")
    void poolableStatus() {
        assertTrue(HouseStatus.POOLABLE.contains(HouseStatus.VACANT));
        assertTrue(HouseStatus.POOLABLE.contains(HouseStatus.PENDING_ALLOC));
        assertFalse(HouseStatus.POOLABLE.contains(HouseStatus.OCCUPIED));
    }

    @Test
    @DisplayName("⭐ 派生指标：空置房源返回 vacantDays")
    void vacantDaysDerived() {
        AssetHouse h = new AssetHouse();
        h.setId(1L);
        h.setHouseStatus("VACANT");
        h.setLockStatusTime(LocalDateTime.now().minusDays(10));
        when(houseMapper.selectById(1L)).thenReturn(h);

        HouseVO vo = houseService.get(1L);
        assertEquals(10L, vo.vacantDays());
        assertEquals("空置待配", vo.houseStatusLabel());
    }

    @Test
    @DisplayName("已入住房源不返回 vacantDays")
    void occupiedNoVacantDays() {
        AssetHouse h = new AssetHouse();
        h.setId(1L);
        h.setHouseStatus("OCCUPIED");
        h.setLockStatusTime(LocalDateTime.now().minusDays(100));
        when(houseMapper.selectById(1L)).thenReturn(h);

        HouseVO vo = houseService.get(1L);
        assertEquals(null, vo.vacantDays(), "非空置状态不应有空置天数");
    }
}
