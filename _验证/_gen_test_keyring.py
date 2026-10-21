# -*- coding: utf-8 -*-
"""生成钥匙包四分类测试 + 对账逻辑测试"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\grant'

KEYRING = r'''package com.yundao.bp.grant;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.yundao.bp.grant.constant.KeyClass;
import com.yundao.bp.grant.constant.KeyType;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 钥匙四分类测试（★ 级「四级权限」核心）。
 *
 * <p><b>为什么必须测</b>：四分类决定安全等级——
 * 实名介质可开大门，非实名介质只能开门锁且必须限期。
 * 分类判错就等于把弱凭证当强凭证用，是安全漏洞。
 */
class KeyringClassTest {

    // ==================== 枚举自身语义 ====================

    @Test
    @DisplayName("四分类齐全：个人/组织 × 实名/非实名")
    void fourClasses() {
        assertEquals(4, KeyClass.values().length);
        assertTrue(KeyClass.PERSONAL_REAL.realName());
        assertFalse(KeyClass.PERSONAL_UNREAL.realName());
        assertTrue(KeyClass.ORG_REAL.realName());
        assertFalse(KeyClass.ORG_UNREAL.realName());
        assertTrue(KeyClass.ORG_REAL.orgOwned());
        assertFalse(KeyClass.PERSONAL_REAL.orgOwned());
    }

    @Test
    @DisplayName("⭐ 只有实名介质允许开大门")
    void onlyRealAllowsMainDoor() {
        assertTrue(KeyClass.PERSONAL_REAL.allowMainDoor());
        assertTrue(KeyClass.ORG_REAL.allowMainDoor());
        assertFalse(KeyClass.PERSONAL_UNREAL.allowMainDoor(),
                "非实名介质绝不可开大门");
        assertFalse(KeyClass.ORG_UNREAL.allowMainDoor());
    }

    @Test
    @DisplayName("⭐ 非实名介质必须设有效期")
    void weakRequiresExpire() {
        assertFalse(KeyClass.PERSONAL_REAL.requireExpireTime());
        assertTrue(KeyClass.PERSONAL_UNREAL.requireExpireTime());
        assertTrue(KeyClass.ORG_UNREAL.requireExpireTime());
    }

    // ==================== 分类推导 ====================

    @Test
    @DisplayName("⭐ 人脸/指纹/掌静脉天然属实名（生物特征不可转让）")
    void biometricIsReal() {
        for (KeyType t : new KeyType[]{KeyType.FACE, KeyType.FINGERPRINT,
                KeyType.PALM_VEIN}) {
            assertEquals(KeyClass.PERSONAL_REAL,
                    KeyClass.derive(t, null, "ADMIN"),
                    t.name() + " 应属个人实名");
        }
    }

    @Test
    @DisplayName("⭐ 密码/卡片默认属非实名（可转借）")
    void passwordCardIsUnreal() {
        assertEquals(KeyClass.PERSONAL_UNREAL,
                KeyClass.derive(KeyType.PASSWORD, null, "ADMIN"));
        assertEquals(KeyClass.PERSONAL_UNREAL,
                KeyClass.derive(KeyType.CARD, null, "ADMIN"));
    }

    @Test
    @DisplayName("⭐ 人证核验通过 → 弱类型也升为实名")
    void faceVerifyUpgrades() {
        // 密码本身弱，但做过人证核验后归属实名
        assertEquals(KeyClass.PERSONAL_REAL,
                KeyClass.derive(KeyType.PASSWORD, "FACE_VERIFY", "SELF_APP"));
    }

    @Test
    @DisplayName("⭐ 身份证下发 → 个人实名")
    void idcardIsReal() {
        assertEquals(KeyClass.PERSONAL_REAL,
                KeyClass.derive(KeyType.IDCARD, null, "IDCARD"));
        // 卡片但来源是身份证下发，视为实名
        assertEquals(KeyClass.PERSONAL_REAL,
                KeyClass.derive(KeyType.CARD, null, "IDCARD"));
    }

    @Test
    @DisplayName("⭐ 组织实名核验 → 组织实名（不是个人实名）")
    void orgVerifyGivesOrgClass() {
        KeyClass c = KeyClass.derive(KeyType.FINGERPRINT, "ORG_VERIFY", "ADMIN");
        assertEquals(KeyClass.ORG_REAL, c);
        assertTrue(c.orgOwned());
        assertTrue(c.allowMainDoor());
    }

    @Test
    @DisplayName("组织核验 + 弱类型 → 组织非实名（不可开大门）")
    void orgWeakIsOrgUnreal() {
        KeyClass c = KeyClass.derive(KeyType.PASSWORD, "ORG_VERIFY", "ADMIN");
        assertEquals(KeyClass.ORG_UNREAL, c);
        assertFalse(c.allowMainDoor());
    }

    @Test
    @DisplayName("未知分类码返回 null（由调用方报错，不静默兜底）")
    void unknownClass() {
        assertEquals(null, KeyClass.of("WHATEVER"));
        assertEquals(KeyClass.PERSONAL_REAL, KeyClass.of("PERSONAL_REAL"));
    }

    // ==================== 钥匙类型映射 IoT 编码 ====================

    @Test
    @DisplayName("⭐ 钥匙类型映射到 IoT 介质编码（下发时直接用，不写 if/else）")
    void keyTypeMapsToIotCode() {
        assertEquals("06", KeyType.FACE.moduleType());
        assertEquals("601", KeyType.FACE.channelType());
        assertEquals("04", KeyType.FINGERPRINT.moduleType());
        assertEquals("401", KeyType.FINGERPRINT.channelType());
        assertEquals("05", KeyType.PALM_VEIN.moduleType());
        assertEquals("01", KeyType.PASSWORD.moduleType());
        assertEquals("02", KeyType.CARD.moduleType());
    }

    @Test
    @DisplayName("每种钥匙类型都有中文标签与编码（无遗漏）")
    void allTypesComplete() {
        for (KeyType t : KeyType.values()) {
            assertTrue(t.label() != null && !t.label().isBlank(), t.name());
            assertTrue(t.moduleType() != null && !t.moduleType().isBlank(), t.name());
            assertTrue(t.channelType() != null && !t.channelType().isBlank(), t.name());
        }
        assertEquals(null, KeyType.of("NOT_A_TYPE"));
    }
}
'''

RECON = r'''package com.yundao.bp.grant;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.grant.entity.GrantEntitlement;
import com.yundao.bp.grant.entity.GrantReconcileDiff;
import com.yundao.bp.grant.entity.GrantTaskDetail;
import com.yundao.bp.grant.mapper.GrantEntitlementMapper;
import com.yundao.bp.grant.mapper.GrantReconcileDiffMapper;
import com.yundao.bp.grant.mapper.GrantTaskDetailMapper;
import com.yundao.bp.grant.service.impl.ReconcileServiceImpl;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
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
 * 授权对账测试。
 *
 * <p><b>为什么必须测</b>：授权是异步下发的，网络抖动/设备离线下会出现
 * 「本地显示已授权、门锁上其实没有」（住户被拒之门外），
 * 或「本地已撤销、门锁上还在」（该失效的没失效，安全风险）。
 * 这两类问题只有在住户刷不开门时才会暴露，必须靠对账主动发现。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ReconcileTest {

    @Mock
    private GrantReconcileDiffMapper diffMapper;
    @Mock
    private GrantEntitlementMapper entitlementMapper;
    @Mock
    private GrantTaskDetailMapper taskDetailMapper;

    private ReconcileServiceImpl service;
    private final List<GrantReconcileDiff> recorded = new ArrayList<>();

    @BeforeEach
    void setUp() {
        service = new ReconcileServiceImpl(diffMapper, entitlementMapper, taskDetailMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(diffMapper.insert(any(GrantReconcileDiff.class))).thenAnswer(inv -> {
            recorded.add(inv.getArgument(0));
            return 1;
        });
        recorded.clear();
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static GrantEntitlement ent(long id, String no, long spaceId, String status,
                                        LocalDateTime end) {
        GrantEntitlement e = new GrantEntitlement();
        e.setId(id);
        e.setGrantNo(no);
        e.setTenantId("350600");
        e.setPersonId(4001L);
        e.setSpaceId(spaceId);
        e.setHouseId(spaceId + 1);
        e.setGrantStatus(status);
        e.setValidStart(LocalDateTime.now().minusDays(10));
        e.setValidEnd(end);
        e.setIsDeleted(0);
        return e;
    }

    private static GrantTaskDetail detail(long spaceId, String lockId, String status) {
        GrantTaskDetail d = new GrantTaskDetail();
        d.setSpaceId(spaceId);
        d.setLockId(lockId);
        d.setDetailStatus(status);
        return d;
    }

    // ==================== 一致性 ====================

    @Test
    @DisplayName("⭐ 有效权益 + 已成功下发 → 一致，无差异")
    void consistent() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "EFFECTIVE", null)));
        when(taskDetailMapper.selectList(any()))
                .thenReturn(List.of(detail(100, "LOCK-A", "SUCCESS")));

        Map<String, Object> r = service.reconcile(null);
        assertEquals(true, r.get("consistent"), String.valueOf(r));
        assertEquals(0, r.get("diffRecorded"));
        assertTrue(recorded.isEmpty(), "一致时不应写差异");
        assertTrue(String.valueOf(r.get("conclusion")).contains("一致"));
    }

    // ==================== ⭐ LOCAL_MISSING ====================

    @Test
    @DisplayName("⭐⭐ 有效权益但锁上无下发记录 → LOCAL_MISSING（住户打不开门）")
    void localMissing() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "EFFECTIVE", null)));
        when(taskDetailMapper.selectList(any())).thenReturn(List.of());

        Map<String, Object> r = service.reconcile(null);
        assertEquals(1, r.get("localMissing"), String.valueOf(r));
        assertEquals(1, r.get("diffRecorded"));
        assertEquals(false, r.get("consistent"));
        assertEquals(1, recorded.size());
        assertEquals("LOCAL_MISSING", recorded.get(0).getDiffType());
        assertEquals("PENDING", recorded.get(0).getHandleStatus());
        assertEquals(4001L, recorded.get(0).getPersonId());
    }

    @Test
    @DisplayName("⭐ 下发失败（非 SUCCESS）等同未下发 → LOCAL_MISSING")
    void failedPushCountsAsMissing() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "EFFECTIVE", null)));
        when(taskDetailMapper.selectList(any()))
                .thenReturn(List.of(detail(100, "LOCK-A", "FAILED")));

        Map<String, Object> r = service.reconcile(null);
        assertEquals(1, r.get("localMissing"), String.valueOf(r));
    }

    @Test
    @DisplayName("⭐ 权益已过期 → 不算「应有」，不产生 LOCAL_MISSING")
    void expiredEntitlementNotExpected() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "EFFECTIVE",
                        LocalDateTime.now().minusDays(1))));
        when(taskDetailMapper.selectList(any())).thenReturn(List.of());

        Map<String, Object> r = service.reconcile(null);
        assertEquals(0, r.get("localMissing"), String.valueOf(r));
    }

    @Test
    @DisplayName("⭐ 权益未到生效日 → 不算「应有」")
    void notStartedNotExpected() {
        GrantEntitlement e = ent(1, "G1", 100, "EFFECTIVE", null);
        e.setValidStart(LocalDateTime.now().plusDays(5));
        when(entitlementMapper.selectList(any())).thenReturn(List.of(e));
        when(taskDetailMapper.selectList(any())).thenReturn(List.of());

        assertEquals(0, service.reconcile(null).get("localMissing"));
    }

    // ==================== ⭐ IOT_EXTRA ====================

    @Test
    @DisplayName("⭐⭐ 权益已撤销但锁上仍有授权 → IOT_EXTRA（安全风险）")
    void iotExtra() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "REVOKED", null)));
        when(taskDetailMapper.selectList(any()))
                .thenReturn(List.of(detail(100, "LOCK-A", "SUCCESS")));

        Map<String, Object> r = service.reconcile(null);
        assertEquals(1, r.get("iotExtra"), String.valueOf(r));
        assertEquals(1, recorded.size());
        assertEquals("IOT_EXTRA", recorded.get(0).getDiffType());
        assertEquals("LOCK-A", recorded.get(0).getLockId());
    }

    @Test
    @DisplayName("⭐ 同一空间多把锁 → 每条差异记一把锁")
    void multipleLocks() {
        when(entitlementMapper.selectList(any()))
                .thenReturn(List.of(ent(1, "G1", 100, "REVOKED", null)));
        when(taskDetailMapper.selectList(any())).thenReturn(List.of(
                detail(100, "LOCK-A", "SUCCESS"),
                detail(100, "LOCK-B", "SUCCESS")));

        Map<String, Object> r = service.reconcile(null);
        assertEquals(2, r.get("iotExtra"), String.valueOf(r));
        assertEquals(2, recorded.size());
    }

    // ==================== 处置 ====================

    private static GrantReconcileDiff pendingDiff(long id, String type) {
        GrantReconcileDiff d = new GrantReconcileDiff();
        d.setId(id);
        d.setDiffType(type);
        d.setHandleStatus("PENDING");
        return d;
    }

    @Test
    @DisplayName("⭐ 处置 LOCAL_MISSING → REGRANT 成功")
    void handleRegrant() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "LOCAL_MISSING"));
        GrantReconcileDiff d = service.handle(9L, "REGRANT", "已重新下发");
        assertEquals("HANDLED", d.getHandleStatus());
        assertEquals("REGRANT", d.getHandleAction());
        assertTrue(d.getHandleTime() != null);
    }

    @Test
    @DisplayName("⭐ 处置 IOT_EXTRA → REVOKE 成功")
    void handleRevoke() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "IOT_EXTRA"));
        assertEquals("HANDLED", service.handle(9L, "REVOKE", "已撤销").getHandleStatus());
    }

    @Test
    @DisplayName("⭐⭐ 动作与差异类型不匹配 → 拒绝（防误操作）")
    void actionTypeMismatch() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "IOT_EXTRA"));
        BizException ex = assertThrows(BizException.class,
                () -> service.handle(9L, "REGRANT", "x"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("重新授权"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 重复处置 → 拒绝")
    void handleTwice() {
        GrantReconcileDiff d = pendingDiff(9, "LOCAL_MISSING");
        d.setHandleStatus("HANDLED");
        when(diffMapper.selectById(9L)).thenReturn(d);
        BizException ex = assertThrows(BizException.class,
                () -> service.handle(9L, "REGRANT", "x"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("忽略处置 → IGNORED（不算已修复）")
    void handleIgnore() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "LOCAL_MISSING"));
        assertEquals("IGNORED", service.handle(9L, "IGNORED", "已知问题").getHandleStatus());
    }

    @Test
    @DisplayName("非法处置动作 → 拒绝")
    void invalidAction() {
        when(diffMapper.selectById(9L)).thenReturn(pendingDiff(9, "LOCAL_MISSING"));
        assertThrows(BizException.class, () -> service.handle(9L, "DELETE", "x"));
    }

    @Test
    @DisplayName("差异不存在 → 404")
    void notFound() {
        when(diffMapper.selectById(9L)).thenReturn(null);
        assertEquals(ErrorCode.NOT_FOUND,
                assertThrows(BizException.class,
                        () -> service.handle(9L, "MANUAL", "x")).errorCode());
    }

    // ==================== 统计 ====================

    @Test
    @DisplayName("⭐⭐ 风险分级：IoT 多余 > 本地缺少 > 无差异")
    void riskLevel() {
        GrantReconcileDiff extra = pendingDiff(1, "IOT_EXTRA");
        GrantReconcileDiff missing = pendingDiff(2, "LOCAL_MISSING");
        when(diffMapper.selectList(any())).thenReturn(List.of(extra, missing));
        Map<String, Object> s = service.stats();
        assertEquals("HIGH", s.get("riskLevel"), String.valueOf(s));
        assertEquals(1, ((Map<?, ?>) s.get("byType")).get("IOT_EXTRA"));

        when(diffMapper.selectList(any())).thenReturn(List.of(missing));
        assertEquals("MEDIUM", service.stats().get("riskLevel"));

        when(diffMapper.selectList(any())).thenReturn(List.of());
        assertEquals("LOW", service.stats().get("riskLevel"));
    }
}
'''

for rel, src in (('KeyringClassTest.java', KEYRING), ('ReconcileTest.java', RECON)):
    p = os.path.join(BASE, rel)
    io.open(p, 'w', encoding='utf-8').write(src)
    print('  + grant/%s（%d 行）' % (rel, src.count('\n')))
