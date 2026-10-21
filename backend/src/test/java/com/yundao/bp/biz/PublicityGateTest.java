package com.yundao.bp.biz;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.LocalDate;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 配租公示门槛测试（决策 D23）。
 *
 * <p><b>业务规则</b>：配租结果必须完成公示（不少于 7 个自然日且已结束），
 * 才能办理签约。<b>这是合规硬校验，不可绕过</b>。
 *
 * <p>此处测的是「公示期判定」这一纯逻辑：给定公示起止日期与当前日期，
 * 判断是否满足「已发布 + 满 7 天 + 已结束」。真实实现中
 * {@code PublicityServiceImpl#hasCompletedAllocationPublicity} 会先查库再调用同样口径。
 */
class PublicityGateTest {

    private static final int MIN_DAYS = 7;

    /**
     * 复刻判定口径：公示已开始、已结束、且跨度 ≥ 最小天数。
     *
     * @param published 是否已发布
     * @param start     公示开始日
     * @param end       公示结束日
     * @param today     当前日期
     */
    private static boolean canSign(boolean published, LocalDate start, LocalDate end,
                                   LocalDate today) {
        if (!published || start == null || end == null) {
            return false;
        }
        // 未开始公示不能签约
        if (today.isBefore(start)) {
            return false;
        }
        // 公示未结束（含今天仍在公示期内）不能签约
        if (!today.isAfter(end)) {
            return false;
        }
        // 跨度不足最小天数不能签约（含首尾，days = end - start + 1）
        long days = end.toEpochDay() - start.toEpochDay() + 1;
        return days >= MIN_DAYS;
    }

    @Test
    @DisplayName("⭐ 已公示 7 天且已结束 → 允许签约")
    void sevenDaysEnded() {
        LocalDate start = LocalDate.of(2026, 10, 1);
        LocalDate end = LocalDate.of(2026, 10, 7);   // 含首尾正好 7 天
        assertTrue(canSign(true, start, end, LocalDate.of(2026, 10, 8)));
    }

    @Test
    @DisplayName("⭐⭐ 公示未结束（今天仍在期内）→ 禁止签约")
    void notEndedBlocks() {
        LocalDate start = LocalDate.of(2026, 10, 1);
        LocalDate end = LocalDate.of(2026, 10, 7);
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 7)),
                "公示最后一天当天不得签约");
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 5)),
                "公示期内不得签约");
    }

    @Test
    @DisplayName("⭐ 公示仅 6 天 → 禁止签约（不足 7 个自然日）")
    void sixDaysBlocks() {
        LocalDate start = LocalDate.of(2026, 10, 1);
        LocalDate end = LocalDate.of(2026, 10, 6);   // 含首尾 6 天
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 10)));
    }

    @Test
    @DisplayName("跨度 7 天但还没结束 → 仍禁止（两个条件都要满足）")
    void longEnoughButNotEnded() {
        LocalDate start = LocalDate.of(2026, 10, 1);
        LocalDate end = LocalDate.of(2026, 10, 20);
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 10)),
                "虽然跨 20 天，但公示未结束");
        assertTrue(canSign(true, start, end, LocalDate.of(2026, 10, 21)));
    }

    @Test
    @DisplayName("⭐ 未发布公示 → 禁止签约")
    void unpublishedBlocks() {
        assertFalse(canSign(false, LocalDate.of(2026, 10, 1),
                LocalDate.of(2026, 10, 7), LocalDate.of(2026, 10, 8)));
    }

    @Test
    @DisplayName("公示尚未开始 → 禁止签约")
    void notStartedBlocks() {
        LocalDate start = LocalDate.of(2026, 11, 1);
        LocalDate end = LocalDate.of(2026, 11, 7);
        assertFalse(canSign(true, start, end, LocalDate.of(2026, 10, 20)));
    }

    @Test
    @DisplayName("缺失公示日期 → 禁止签约（不能默认放行）")
    void nullDatesBlock() {
        assertFalse(canSign(true, null, null, LocalDate.now()));
        assertFalse(canSign(true, LocalDate.now(), null, LocalDate.now()));
    }

    @Test
    @DisplayName("⭐ 缺省必须拒绝：宁可挡住业务，也不能违规签约")
    void failClosed() {
        // 各种「信息不全」场景一律拒绝
        assertFalse(canSign(false, null, null, null == null ? LocalDate.now() : null));
        assertFalse(canSign(true, LocalDate.of(2026, 10, 1), LocalDate.of(2026, 10, 7),
                LocalDate.of(2026, 9, 30)));
    }

    @Test
    @DisplayName("跨越月份/年末也不受影响（按自然日算）")
    void crossMonth() {
        // 2026-12-28 ~ 2027-01-03 含首尾 = 7 天
        LocalDate start = LocalDate.of(2026, 12, 28);
        LocalDate end = LocalDate.of(2027, 1, 3);
        assertTrue(canSign(true, start, end, LocalDate.of(2027, 1, 4)));
    }

    @Test
    @DisplayName("公示期很长也应允许（≥7 天即可，无上限）")
    void veryLongOk() {
        assertTrue(canSign(true, LocalDate.of(2026, 1, 1),
                LocalDate.of(2026, 3, 1), LocalDate.of(2026, 3, 2)));
    }
}
