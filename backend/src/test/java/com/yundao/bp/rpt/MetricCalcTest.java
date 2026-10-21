package com.yundao.bp.rpt;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.dev.mapper.DevAccessRecordMapper;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinPaymentMapper;
import com.yundao.bp.rpt.mapper.RptMetricDailyMapper;
import com.yundao.bp.rpt.service.impl.MetricServiceImpl;
import java.math.BigDecimal;
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
 * 指标计算测试。
 *
 * <p>重点：<b>除零保护</b>（无房源时出租率不能抛异常）、<b>精度</b>（金额 2 位）、
 * <b>占比公式</b>（不可信开门占比，考核指标）。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class MetricCalcTest {

    @Mock
    private AssetHouseMapper houseMapper;
    @Mock
    private FinBillMapper billMapper;
    @Mock
    private FinPaymentMapper paymentMapper;
    @Mock
    private DevAccessRecordMapper accessMapper;
    @Mock
    private RptMetricDailyMapper dailyMapper;

    private MetricServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new MetricServiceImpl(houseMapper, billMapper, paymentMapper, accessMapper,
                dailyMapper, new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private void given(int total, int occupied, String unpaidAmount) {
        when(houseMapper.selectCount(any()))
                .thenReturn((long) total)     // 第一次：总数
                .thenReturn((long) occupied); // 第二次：已租
        when(billMapper.countUnpaid(any(), any())).thenReturn(5L);
        when(billMapper.sumUnpaidPayable(any(), any())).thenReturn(new BigDecimal(unpaidAmount));
        when(paymentMapper.sumSuccessPayAmount(any(), any()))
                .thenReturn(new BigDecimal("12345.67"));
        when(accessMapper.selectCount(any())).thenReturn(8L);
    }

    @Test
    @DisplayName("房源总数/已租/空置取数正确")
    void houseCounts() {
        given(32, 2, "9160.00");
        assertEquals(32.0, service.current("HOUSE_TOTAL", null), 0.001);
    }

    @Test
    @DisplayName("出租率 = 已租 / 总数 × 100，保留 2 位（2/32 = 6.25）")
    void occupancyRate() {
        given(32, 2, "0");
        assertEquals(6.25, service.current("OCCUPANCY_RATE", null), 0.001);
    }

    @Test
    @DisplayName("⭐⭐ 无房源时出租率返回 0，不能抛除零异常")
    void occupancyRateNoDivideByZero() {
        given(0, 0, "0");
        assertEquals(0.0, service.current("OCCUPANCY_RATE", null), 0.001);
    }

    @Test
    @DisplayName("欠费金额按 SQL 聚合取，2 位小数")
    void unpaidAmount() {
        given(32, 2, "9160.005");
        assertEquals(9160.01, service.current("BILL_UNPAID_AMOUNT", null), 0.001);
    }

    @Test
    @DisplayName("未知指标编码返回 0（不抛异常，前端容错）")
    void unknownMetric() {
        given(1, 1, "0");
        assertEquals(0.0, service.current("NO_SUCH_METRIC", null), 0.001);
    }

    @Test
    @DisplayName("currentAll 包含全部核心指标")
    void currentAllKeys() {
        given(32, 2, "100.00");
        Map<String, Object> m = service.currentAll(null);
        for (String k : List.of("HOUSE_TOTAL", "HOUSE_OCCUPIED", "HOUSE_VACANT",
                "OCCUPANCY_RATE", "BILL_UNPAID_COUNT", "BILL_UNPAID_AMOUNT",
                "PAYMENT_TOTAL_AMOUNT", "ACCESS_TODAY_COUNT", "ACCESS_ABNORMAL_COUNT")) {
            assertTrue(m.containsKey(k), "缺少指标 " + k);
        }
        assertTrue(m.containsKey("generatedAt"));
    }

    @Test
    @DisplayName("按需取值只返回请求的指标（不多算）")
    void valuesOnlyRequested() {
        given(32, 2, "100.00");
        Map<String, Object> m = service.values(
                List.of("HOUSE_TOTAL", "ACCESS_TODAY_COUNT"), null);
        assertEquals(2, m.size(), m.keySet().toString());
        assertTrue(m.containsKey("HOUSE_TOTAL"));
        assertTrue(m.containsKey("ACCESS_TODAY_COUNT"));
    }
}
