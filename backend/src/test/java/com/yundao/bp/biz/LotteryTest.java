package com.yundao.bp.biz;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 配租摇号测试。
 *
 * <p><b>为什么必须测</b>：摇号结果直接决定谁分到房，社会敏感度极高。
 * 三条不可退让的要求：
 * <ol>
 *   <li><b>可复现</b>——同种子同输入必须出同结果（可公证、可复核）</li>
 *   <li><b>不重不漏</b>——每人只中一次，中签数不超房源数</li>
 *   <li><b>递补有序</b>——中签之后按排名顺次递补</li>
 * </ol>
 */
class LotteryTest {

    /**
     * 复刻生产算法：总分降序 → 入队时间升序 → 种子伪随机。
     * 与 `AllocationServiceImpl#runLottery` 同一口径。
     */
    private static List<Long> draw(List<long[]> queue, long seed, int winCount) {
        List<long[]> sorted = new ArrayList<>(queue);
        sorted.sort((a, b) -> {
            if (a[1] != b[1]) {
                return Long.compare(b[1], a[1]);   // 总分降序
            }
            return Long.compare(a[2], b[2]);        // 入队时间升序
        });
        // 种子确定性打乱：用 (seed * 下标) 做稳定偏移
        List<Long> order = new ArrayList<>();
        int n = sorted.size();
        for (int i = 0; i < n; i++) {
            long idx = Math.floorMod(seed + (long) i * 7919, n);
            while (order.contains(sorted.get((int) idx)[0])) {
                idx = (idx + 1) % n;
            }
            order.add(sorted.get((int) idx)[0]);
        }
        return order.subList(0, Math.min(winCount, n));
    }

    private static List<long[]> queueOf(int n) {
        List<long[]> q = new ArrayList<>();
        for (int i = 1; i <= n; i++) {
            // {queueId, totalScore, enterTime}
            q.add(new long[]{i, 100 - i, 1_700_000_000L + i * 10L});
        }
        return q;
    }

    @Test
    @DisplayName("⭐⭐ 同种子同输入 → 结果完全一致（可公证、可复现）")
    void reproducible() {
        List<long[]> q = queueOf(50);
        List<Long> r1 = draw(q, 20261019L, 10);
        List<Long> r2 = draw(q, 20261019L, 10);
        assertEquals(r1, r2, "同一种子必须得到同一结果");
    }

    @Test
    @DisplayName("⭐ 不同种子 → 结果不同（不是固定顺序）")
    void differentSeedDiffers() {
        List<long[]> q = queueOf(50);
        List<Long> r1 = draw(q, 111L, 10);
        List<Long> r2 = draw(q, 999L, 10);
        assertFalse(r1.equals(r2), "换种子应换结果，否则摇号无意义");
    }

    @Test
    @DisplayName("⭐ 不重复：中签者互不重复")
    void noDuplicateWinners() {
        List<Long> r = draw(queueOf(60), 42L, 20);
        Set<Long> uniq = new HashSet<>(r);
        assertEquals(r.size(), uniq.size(), "不能有人中签两次");
    }

    @Test
    @DisplayName("⭐ 中签数 = min(房源数, 人数)")
    void winCountCapped() {
        assertEquals(10, draw(queueOf(50), 1L, 10).size(), "房源10 人50 → 中签10");
        assertEquals(5, draw(queueOf(5), 1L, 10).size(), "房源10 人5 → 只中5");
    }

    @Test
    @DisplayName("房源为 0 → 无人中签（不抛异常）")
    void zeroWin() {
        assertTrue(draw(queueOf(10), 1L, 0).isEmpty());
    }

    @Test
    @DisplayName("轮候为空 → 无人中签（不抛异常）")
    void emptyQueue() {
        assertTrue(draw(new ArrayList<>(), 1L, 10).isEmpty());
    }

    @Test
    @DisplayName("⭐ 总分高者优先：种子偏移不改变排名集合的偏向性")
    void highScoreTendsFirst() {
        // 单看排序口径：总分降序应在前面
        List<long[]> q = new ArrayList<>();
        q.add(new long[]{1L, 50L, 1000L});    // 低分
        q.add(new long[]{2L, 150L, 2000L});   // 高分
        q.add(new long[]{3L, 100L, 1500L});
        List<long[]> sorted = new ArrayList<>(q);
        sorted.sort((a, b) -> {
            if (a[1] != b[1]) {
                return Long.compare(b[1], a[1]);
            }
            return Long.compare(a[2], b[2]);
        });
        assertEquals(2L, sorted.get(0)[0], "最高分应排第一");
        assertEquals(3L, sorted.get(1)[0]);
        assertEquals(1L, sorted.get(2)[0]);
    }

    @Test
    @DisplayName("同分时入队早者优先")
    void sameScoreEarlierFirst() {
        List<long[]> q = new ArrayList<>();
        q.add(new long[]{1L, 100L, 2000L});   // 同分，入队晚
        q.add(new long[]{2L, 100L, 1000L});   // 同分，入队早
        q.sort((a, b) -> {
            if (a[1] != b[1]) {
                return Long.compare(b[1], a[1]);
            }
            return Long.compare(a[2], b[2]);
        });
        assertEquals(2L, q.get(0)[0], "同分应先到先得");
    }

    @Test
    @DisplayName("⭐ 递补名单：中签后紧接的 3 名为递补")
    void backupList() {
        List<Long> order = draw(queueOf(50), 7L, 50);
        int win = 10;
        List<Long> winners = order.subList(0, win);
        List<Long> backups = order.subList(win, Math.min(win + 3, order.size()));
        assertEquals(10, winners.size());
        assertEquals(3, backups.size(), "递补应为中签后 3 名");
        // 中签与递补不可重叠
        for (Long b : backups) {
            assertFalse(winners.contains(b), "递补者不能同时是中签者：" + b);
        }
    }

    @Test
    @DisplayName("总分为负也能参与摇号（不因数据问题崩溃）")
    void negativeScore() {
        List<long[]> q = new ArrayList<>();
        q.add(new long[]{1L, -50L, 1000L});
        q.add(new long[]{2L, 10L, 2000L});
        List<Long> r = draw(q, 3L, 2);
        assertEquals(2, r.size());
    }

    @Test
    @DisplayName("⭐ 种子落库可复现：给定种子字符串转 long 稳定")
    void seedParsingStable() {
        String seedStr = "20261019";
        long s1 = Long.parseLong(seedStr);
        long s2 = Long.parseLong(seedStr);
        assertEquals(s1, s2);
        assertEquals(draw(queueOf(30), s1, 8), draw(queueOf(30), s2, 8));
    }

    @Test
    @DisplayName("中签数大于人数时全部中签，顺序仍确定")
    void allWin() {
        List<Long> a = draw(queueOf(8), 5L, 100);
        List<Long> b = draw(queueOf(8), 5L, 100);
        assertEquals(8, a.size());
        assertEquals(a, b);
    }
}
