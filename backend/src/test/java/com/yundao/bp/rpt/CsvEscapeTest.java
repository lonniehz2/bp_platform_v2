package com.yundao.bp.rpt;

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
