package com.yundao.bp.grant;

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
