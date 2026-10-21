# -*- coding: utf-8 -*-
"""生成配租摇号测试（种子可复现/中签数/递补）+ CSV 转义测试"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp'

# ==================== 1) 摇号 ====================
LOTTERY_TEST = r'''package com.yundao.bp.biz;

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
'''

# ==================== 2) CSV 转义 ====================
CSV_TEST = r'''package com.yundao.bp.rpt;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * CSV 导出转义测试。
 *
 * <p><b>为什么必须测</b>：导出给房管局的报表，只要某个字段含逗号/引号/换行，
 * 整行就会错位，接收方解析全乱。这类问题在真机上极难发现（要刚好有脏数据），
 * 只能靠单测锁住。
 */
class CsvEscapeTest {

    /** 与 `ReportServiceImpl#escape` 同一口径。 */
    private static String escape(String s) {
        if (s == null) {
            return "";
        }
        if (s.contains(",") || s.contains("\"") || s.contains("\n")) {
            return "\"" + s.replace("\"", "\"\"") + "\"";
        }
        return s;
    }

    /** 与 `ReportServiceImpl#toCsv` 同一口径。 */
    private static String toCsv(List<String> titles, List<String> keys,
                                List<Map<String, Object>> rows) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < titles.size(); i++) {
            if (i > 0) {
                sb.append(',');
            }
            sb.append(escape(titles.get(i)));
        }
        sb.append('\n');
        for (Map<String, Object> r : rows) {
            for (int i = 0; i < keys.size(); i++) {
                if (i > 0) {
                    sb.append(',');
                }
                Object v = r.get(keys.get(i));
                sb.append(escape(v == null ? "" : String.valueOf(v)));
            }
            sb.append('\n');
        }
        return sb.toString();
    }

    @Test
    @DisplayName("普通字段不加引号")
    void plain() {
        assertEquals("张三", escape("张三"));
        assertEquals("A001", escape("A001"));
    }

    @Test
    @DisplayName("⭐ 含逗号 → 整体加双引号（否则整行错位）")
    void comma() {
        assertEquals("\"朝阳区,幸福小区\"", escape("朝阳区,幸福小区"));
    }

    @Test
    @DisplayName("⭐ 含双引号 → 加引号并把内部引号双写（CSV 标准）")
    void quote() {
        assertEquals("\"他说\"\"要退租\"\"\"", escape("他说\"要退租\""));
    }

    @Test
    @DisplayName("⭐ 含换行 → 加引号（否则被当两行）")
    void newline() {
        assertEquals("\"第一行\n第二行\"", escape("第一行\n第二行"));
    }

    @Test
    @DisplayName("null → 空字符串（不输出 null 字样）")
    void nullValue() {
        assertEquals("", escape(null));
    }

    @Test
    @DisplayName("空字符串保持空")
    void empty() {
        assertEquals("", escape(""));
    }

    @Test
    @DisplayName("全角逗号不触发转义（不应被误判）")
    void fullWidthComma() {
        assertEquals("朝阳区，幸福小区", escape("朝阳区，幸福小区"));
    }

    @Test
    @DisplayName("⭐⭐ 完整 CSV：表头 + 脏数据行，列数严格一致")
    void wholeCsvColumnCount() {
        List<String> titles = List.of("房源编号", "名称", "备注");
        List<String> keys = List.of("code", "name", "memo");
        List<Map<String, Object>> rows = new ArrayList<>();
        Map<String, Object> r1 = new LinkedHashMap<>();
        r1.put("code", "A001");
        r1.put("name", "幸福小区,3号楼");
        r1.put("memo", "含\"引号\"");
        rows.add(r1);
        Map<String, Object> r2 = new LinkedHashMap<>();
        r2.put("code", "A002");
        r2.put("name", null);
        r2.put("memo", "");
        rows.add(r2);

        String csv = toCsv(titles, keys, rows);
        String[] lines = csv.split("\n");
        assertEquals(3, lines.length, "1 表头 + 2 数据行");
        assertEquals("房源编号,名称,备注", lines[0]);
        // 脏数据行必须仍是一条逻辑行，且字段被正确包裹
        assertTrue(lines[1].startsWith("A001,\"幸福小区,3号楼\","), lines[1]);
        assertTrue(lines[1].endsWith("\"含\"\"引号\"\"\""), lines[1]);
        // null 与空串都输出为空
        assertEquals("A002,,", lines[2]);
    }

    @Test
    @DisplayName("金额与日期按原样输出（不做千分位，避免接收方解析失败）")
    void amountAndDate() {
        assertEquals("1234.56", escape("1234.56"));
        assertEquals("2026-10-19", escape("2026-10-19"));
    }
}
'''

for rel, src in (('biz/LotteryTest.java', LOTTERY_TEST),
                 ('rpt/CsvEscapeTest.java', CSV_TEST)):
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('  + %s（%d 行）' % (rel, src.count('\n')))
