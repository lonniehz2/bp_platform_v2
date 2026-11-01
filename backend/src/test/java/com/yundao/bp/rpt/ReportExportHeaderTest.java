package com.yundao.bp.rpt;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.yundao.bp.common.i18n.LocaleContext;
import com.yundao.bp.rpt.service.impl.ReportServiceImpl;
import java.lang.reflect.Method;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

/** 导出表头必须跟随请求语言，避免英文导出仍输出中文列名。 */
class ReportExportHeaderTest {

    @AfterEach
    void clear() {
        LocaleContext.clear();
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, String>> columns(String code) throws Exception {
        ReportServiceImpl svc = new ReportServiceImpl(null, null, null, null, null, null, "/tmp");
        Method m = ReportServiceImpl.class.getDeclaredMethod("columnsOf", String.class);
        m.setAccessible(true);
        return (List<Map<String, String>>) m.invoke(svc, code);
    }

    @Test
    void englishHeaders() throws Exception {
        LocaleContext.set(Locale.US);
        List<Map<String, String>> cols = columns("HOUSE_LEDGER");
        assertEquals(5, cols.size());
        assertEquals("Housing Code", cols.get(0).get("title"));
        assertEquals("Area (m²)", cols.get(3).get("title"));
        assertEquals("Housing Status", cols.get(4).get("title"));
    }

    @Test
    void chineseHeaders() throws Exception {
        LocaleContext.set(Locale.SIMPLIFIED_CHINESE);
        List<Map<String, String>> cols = columns("CONTRACT_LEDGER");
        assertEquals("合同号", cols.get(0).get("title"));
        assertEquals("承租人", cols.get(1).get("title"));
    }
}
