package com.yundao.bp.person;

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
import com.yundao.bp.person.constant.IncomeLevel;
import com.yundao.bp.person.entity.PersonGuaranteeProfile;
import com.yundao.bp.person.mapper.PersonGuaranteeProfileMapper;
import com.yundao.bp.person.service.GuaranteeProfileService;
import com.yundao.bp.person.service.impl.GuaranteeProfileServiceImpl;
import java.math.BigDecimal;
import java.time.LocalDate;
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
 * 保障对象档案测试。
 *
 * <p>重点：<b>人均收入档位判定</b>（分地区阈值不同）、<b>资格有效期</b>、
 * <b>到期预警</b>。这些直接决定能否享受保障与补贴额度。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class GuaranteeProfileTest {

    @Mock
    private PersonGuaranteeProfileMapper mapper;

    private GuaranteeProfileServiceImpl service;

    private static final BigDecimal LOW = new BigDecimal("1200");
    private static final BigDecimal LOW_INCOME = new BigDecimal("2400");
    private static final BigDecimal MIDDLE_LOW = new BigDecimal("4000");

    @BeforeEach
    void setUp() {
        service = new GuaranteeProfileServiceImpl(mapper, new SnowflakeIdGenerator(1, 1),
                org.mockito.Mockito.mock(com.yundao.bp.person.mapper.PersonMapper.class));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(mapper.insert(any(PersonGuaranteeProfile.class))).thenReturn(1);
        when(mapper.updateById(any(PersonGuaranteeProfile.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static PersonGuaranteeProfile profile(String income, int size, String level,
                                                  LocalDate expire, String status) {
        PersonGuaranteeProfile e = new PersonGuaranteeProfile();
        e.setId(1L);
        e.setTenantId("350600");
        e.setPersonId(4001L);
        e.setSecurityType("PUBLIC");
        e.setFamilySize(size);
        e.setMonthlyIncome(income == null ? null : new BigDecimal(income));
        e.setIncomeLevel(level);
        e.setProfileStatus(status);
        e.setQualifyExpire(expire);
        e.setIsDeleted(0);
        return e;
    }

    // ==================== 收入档位（纯逻辑） ====================

    @Test
    @DisplayName("⭐⭐ 人均收入 ≤ 低保线 → LOW（3 人 3000 元 = 人均 1000）")
    void lowLevel() {
        assertEquals(IncomeLevel.LOW, IncomeLevel.of(new BigDecimal("3000"), 3,
                LOW, LOW_INCOME, MIDDLE_LOW));
    }

    @Test
    @DisplayName("⭐ 人均在低保与低收入线之间 → LOW_INCOME")
    void lowIncomeLevel() {
        // 人均 1500：>1200 且 <=2400
        assertEquals(IncomeLevel.LOW_INCOME,
                IncomeLevel.of(new BigDecimal("4500"), 3, LOW, LOW_INCOME, MIDDLE_LOW));
    }

    @Test
    @DisplayName("⭐ 人均在中低收入线内 → MIDDLE_LOW")
    void middleLowLevel() {
        // 人均 3000
        assertEquals(IncomeLevel.MIDDLE_LOW,
                IncomeLevel.of(new BigDecimal("6000"), 2, LOW, LOW_INCOME, MIDDLE_LOW));
    }

    @Test
    @DisplayName("超过中低收入线 → NORMAL（不符合保障条件）")
    void normalLevel() {
        // 人均 5000
        assertEquals(IncomeLevel.NORMAL, IncomeLevel.of(new BigDecimal("10000"), 2,
                LOW, LOW_INCOME, MIDDLE_LOW));
    }

    @Test
    @DisplayName("⭐⭐ 边界：人均恰好等于低保线算 LOW（<= 语义）")
    void boundaryEqualsLowLine() {
        assertEquals(IncomeLevel.LOW,
                IncomeLevel.of(new BigDecimal("2400"), 2, LOW, LOW_INCOME, MIDDLE_LOW));
    }

    @Test
    @DisplayName("⭐ 高收入者不能因人多而被平均进低保（人均口径防作弊）")
    void perCapitaNotTotal() {
        // 家庭月入 20000，5 人 → 人均 4000 → 恰好中低收入线
        assertEquals(IncomeLevel.MIDDLE_LOW, IncomeLevel.of(new BigDecimal("20000"), 5,
                LOW, LOW_INCOME, MIDDLE_LOW));
        // 若误用总额（20000）判定，会被判为 NORMAL
    }

    @Test
    @DisplayName("缺收入 → NORMAL（不默认给低保）")
    void nullIncome() {
        assertEquals(IncomeLevel.NORMAL,
                IncomeLevel.of(null, 3, LOW, LOW_INCOME, MIDDLE_LOW));
    }

    @Test
    @DisplayName("⭐ 人口为 0/null 时按 1 人算（除零保护）")
    void zeroFamilySize() {
        assertEquals(IncomeLevel.LOW, IncomeLevel.of(new BigDecimal("1000"), 0,
                LOW, LOW_INCOME, MIDDLE_LOW));
        assertEquals(IncomeLevel.LOW, IncomeLevel.of(new BigDecimal("1000"), null,
                LOW, LOW_INCOME, MIDDLE_LOW));
    }

    @Test
    @DisplayName("⭐ 阈值未配置时不误判（缺线则跳过该档）")
    void nullThresholds() {
        assertEquals(IncomeLevel.NORMAL,
                IncomeLevel.of(new BigDecimal("500"), 1, null, null, null));
    }

    // ==================== 建档校验 ====================

    @Test
    @DisplayName("⭐ 家庭人口为 0 → 拒绝（否则按人计费算成 0）")
    void rejectZeroFamilySize() {
        when(mapper.selectOne(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class, () -> service.save(
                new GuaranteeProfileService.ProfileCmd(4001L, "PUBLIC", 0, "SINGLE",
                        new BigDecimal("3000"), null, 0, 0, 0, null, null, null, null)));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
        assertTrue(ex.getMessage().contains("家庭人口"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 月收入为负 → 拒绝")
    void rejectNegativeIncome() {
        when(mapper.selectOne(any())).thenReturn(null);
        assertThrows(BizException.class, () -> service.save(
                new GuaranteeProfileService.ProfileCmd(4001L, "PUBLIC", 2, "COUPLE",
                        new BigDecimal("-100"), null, 0, 0, 0, null, null, null, null)));
    }

    @Test
    @DisplayName("缺保障类型 → 拒绝")
    void rejectNoSecurityType() {
        when(mapper.selectOne(any())).thenReturn(null);
        assertThrows(BizException.class, () -> service.save(
                new GuaranteeProfileService.ProfileCmd(4001L, null, 2, null, null, null,
                        0, 0, 0, null, null, null, null)));
    }

    // ==================== 资格 ====================

    @Test
    @DisplayName("⭐ 审核通过 → QUALIFIED 并写资格有效期")
    void qualify() {
        when(mapper.selectOne(any())).thenReturn(
                profile("3000", 3, "LOW", null, "APPLICANT"));
        PersonGuaranteeProfile e = service.qualify(4001L, 1);
        assertEquals("QUALIFIED", e.getProfileStatus());
        assertEquals(LocalDate.now(), e.getQualifyDate());
        assertEquals(LocalDate.now().plusYears(1), e.getQualifyExpire());
    }

    @Test
    @DisplayName("⭐ 已退出的档案不可再通过审核")
    void cannotQualifyExited() {
        when(mapper.selectOne(any())).thenReturn(
                profile("3000", 3, "LOW", null, "EXITED"));
        BizException ex = assertThrows(BizException.class, () -> service.qualify(4001L, 1));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("⭐ 重复退出 → 拒绝")
    void cannotExitTwice() {
        when(mapper.selectOne(any())).thenReturn(
                profile("3000", 3, "LOW", null, "EXITED"));
        assertThrows(BizException.class,
                () -> service.exit(4001L, LocalDate.now(), "x"));
    }

    @Test
    @DisplayName("退出记录日期与原因")
    void exit() {
        when(mapper.selectOne(any())).thenReturn(
                profile("3000", 3, "LOW", null, "IN_RESIDENCE"));
        PersonGuaranteeProfile e = service.exit(4001L, LocalDate.now(), "购买住房");
        assertEquals("EXITED", e.getProfileStatus());
        assertEquals("购买住房", e.getExitReason());
    }

    // ==================== ⭐ 到期预警 ====================

    @Test
    @DisplayName("⭐⭐ 资格到期预警：已过期标记 expired=true 并给出处置建议")
    void expiredWarning() {
        when(mapper.selectList(any())).thenReturn(List.of(
                profile("3000", 3, "LOW", LocalDate.now().minusDays(10), "QUALIFIED")));
        List<Map<String, Object>> list = service.expiring(30);
        assertEquals(1, list.size());
        Map<String, Object> m = list.get(0);
        assertEquals(true, m.get("expired"));
        assertEquals(-10L, m.get("daysLeft"));
        assertTrue(String.valueOf(m.get("advice")).contains("已过期"),
                    String.valueOf(m.get("advice")));
    }

    @Test
    @DisplayName("⭐ 即将到期（还剩 15 天）→ expired=false，建议安排复核")
    void expiringSoon() {
        when(mapper.selectList(any())).thenReturn(List.of(
                profile("3000", 3, "LOW", LocalDate.now().plusDays(15), "QUALIFIED")));
        Map<String, Object> m = service.expiring(30).get(0);
        assertEquals(false, m.get("expired"));
        assertEquals(15L, m.get("daysLeft"));
        assertTrue(String.valueOf(m.get("advice")).contains("复核"),
                    String.valueOf(m.get("advice")));
    }

    @Test
    @DisplayName("无到期档案 → 空列表")
    void noExpiring() {
        when(mapper.selectList(any())).thenReturn(List.of());
        assertTrue(service.expiring(30).isEmpty());
    }

    // ==================== 收入重算 ====================

    @Test
    @DisplayName("⭐ 收入重算：档位变化时 changed=true")
    void recalcIncomeChanged() {
        when(mapper.selectOne(any())).thenReturn(
                profile("3000", 3, "NORMAL", null, "APPLICANT"));
        Map<String, Object> r = service.recalcIncome(4001L, LOW, LOW_INCOME, MIDDLE_LOW);
        assertEquals("NORMAL", r.get("incomeLevelBefore"));
        assertEquals("LOW", r.get("incomeLevelAfter"));
        assertEquals(true, r.get("changed"));
        assertEquals(0, new BigDecimal("1000").compareTo(
                (BigDecimal) r.get("perCapitaIncome")));
    }

    @Test
    @DisplayName("档位不变时 changed=false")
    void recalcIncomeUnchanged() {
        when(mapper.selectOne(any())).thenReturn(
                profile("3000", 3, "LOW", null, "APPLICANT"));
        assertEquals(false,
                service.recalcIncome(4001L, LOW, LOW_INCOME, MIDDLE_LOW).get("changed"));
    }
}
