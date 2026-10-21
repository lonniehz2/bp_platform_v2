package com.yundao.bp.fin;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizContractCohabitant;
import com.yundao.bp.biz.mapper.BizContractCohabitantMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.fin.dto.SubsidyCalcCmd;
import com.yundao.bp.fin.entity.FinSubsidyStandard;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinSubsidyRecordMapper;
import com.yundao.bp.fin.mapper.FinSubsidyStandardMapper;
import com.yundao.bp.fin.service.SubsidyService;
import com.yundao.bp.fin.service.impl.SubsidyServiceImpl;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * 补贴计算测试。
 *
 * <p>补贴直接决定财政支出与住户到手金额，算错即错发钱。
 * 覆盖 <b>4 种补贴方式 + 月度封顶 + 按人取同住人 + 缺数据报错</b>。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class SubsidyCalcTest {

    @Mock
    private FinSubsidyStandardMapper standardMapper;
    @Mock
    private FinSubsidyRecordMapper recordMapper;
    @Mock
    private FinBillMapper billMapper;
    @Mock
    private BizContractMapper contractMapper;
    @Mock
    private AssetHouseMapper houseMapper;
    @Mock
    private BizContractCohabitantMapper cohabitantMapper;

    private SubsidyServiceImpl service;

    private static FinSubsidyStandard std(String mode, String value, String cap) {
        FinSubsidyStandard s = new FinSubsidyStandard();
        s.setId(10L);
        s.setStandardCode("SUB-" + mode);
        s.setStandardName("测试标准");
        s.setSecurityType("PUBLIC");
        s.setSubsidyMode(mode);
        s.setSubsidyValue(new BigDecimal(value));
        s.setMaxAmount(cap == null ? null : new BigDecimal(cap));
        s.setStatus("ENABLED");
        s.setEffectiveStart(LocalDate.now().minusDays(1));
        return s;
    }

    private static BizContract contract() {
        BizContract c = new BizContract();
        c.setId(2001L);
        c.setContractNo("BC2001");
        c.setTenantId("350600");
        c.setOrgId(7001L);
        c.setHouseId(5001L);
        c.setLesseePersonId(4001L);
        c.setLesseeName("张三");
        c.setContractType("PUBLIC_RENTAL");
        c.setMonthlyRent(new BigDecimal("1000"));
        c.setContractStatus("EFFECTIVE");
        return c;
    }

    private void givenStandard(FinSubsidyStandard s) {
        when(contractMapper.selectById(2001L)).thenReturn(contract());
        when(standardMapper.selectList(any())).thenReturn(List.of(s));
        when(standardMapper.selectById(10L)).thenReturn(s);
    }

    @BeforeEach
    void setUp() {
        service = new SubsidyServiceImpl(standardMapper, recordMapper, billMapper,
                contractMapper, houseMapper, new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        AssetHouse h = new AssetHouse();
        h.setId(5001L);
        h.setArea(new BigDecimal("80"));
        when(houseMapper.selectById(5001L)).thenReturn(h);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private SubsidyService.SubsidyCalcResult preview(SubsidyCalcCmd cmd) {
        return service.preview(cmd);
    }

    // ==================== 4 种方式 ====================

    @Test
    @DisplayName("FIXED 定额：800 → 800.00")
    void fixed() {
        givenStandard(std("FIXED", "800", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("800").compareTo(r.cappedAmount()));
        assertFalse(r.capped());
    }

    @Test
    @DisplayName("BY_AREA 按面积：20 × 80㎡ = 1600，封顶 1500 → 1500.00 且 capped=true")
    void byAreaWithCap() {
        givenStandard(std("BY_AREA", "20", "1500"));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("1600").compareTo(r.amount()), "封顶前应为 1600");
        assertEquals(0, new BigDecimal("1500").compareTo(r.cappedAmount()), "封顶后应为 1500");
        assertTrue(r.capped());
        assertTrue(r.explain().contains("封顶"), r.explain());
    }

    @Test
    @DisplayName("BY_AREA：未达封顶时原样（20 × 50 = 1000）")
    void byAreaUnderCap() {
        givenStandard(std("BY_AREA", "20", "1500"));
        var r = preview(new SubsidyCalcCmd(2001L, null, new BigDecimal("50"), null, null));
        assertEquals(0, new BigDecimal("1000").compareTo(r.cappedAmount()));
        assertFalse(r.capped());
    }

    @Test
    @DisplayName("BY_PERSON 按人：300 × 3 人 = 900.00（显式传人数）")
    void byPersonExplicit() {
        givenStandard(std("BY_PERSON", "300", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, 3, null));
        assertEquals(0, new BigDecimal("900").compareTo(r.cappedAmount()));
    }

    @Test
    @DisplayName("⭐BY_PERSON 未传人数 → 从同住人取（1 承租人 + 2 同住 = 3 人 → 900.00）")
    void byPersonFromCohabitants() {
        givenStandard(std("BY_PERSON", "300", null));
        ReflectionTestUtils.setField(service, "cohabitantMapper", cohabitantMapper);
        when(cohabitantMapper.selectCount(any())).thenReturn(2L);

        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("900").compareTo(r.cappedAmount()),
                "保障人口应为 1+2=3，实际结果 " + r.cappedAmount());
        assertTrue(r.explain().contains("3 人"), r.explain());
    }

    @Test
    @DisplayName("⭐BY_PERSON 无同住人信息时兜底 1 人（不报错）")
    void byPersonFallbackOne() {
        givenStandard(std("BY_PERSON", "300", null));
        // cohabitantMapper 未注入（null）→ 兜底 1 人
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("300").compareTo(r.cappedAmount()));
    }

    @Test
    @DisplayName("RATIO 按租金比例：1000 × 0.6 = 600.00")
    void ratio() {
        givenStandard(std("RATIO", "0.6", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertEquals(0, new BigDecimal("600").compareTo(r.cappedAmount()));
    }

    @Test
    @DisplayName("RATIO 可覆盖月租金参与计算（1200 × 0.6 = 720.00）")
    void ratioWithExplicitRent() {
        givenStandard(std("RATIO", "0.6", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, new BigDecimal("1200")));
        assertEquals(0, new BigDecimal("720").compareTo(r.cappedAmount()));
    }

    // ==================== 缺数据 / 异常 ====================

    @Test
    @DisplayName("⭐BY_AREA 但房源无面积 → 明确报错（含合同号与房源ID）")
    void byAreaNoArea() {
        givenStandard(std("BY_AREA", "20", null));
        AssetHouse h = new AssetHouse();
        h.setId(5001L);
        h.setArea(null);
        when(houseMapper.selectById(5001L)).thenReturn(h);

        BizException ex = assertThrows(BizException.class,
                () -> preview(new SubsidyCalcCmd(2001L, null, null, null, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("面积"), ex.getMessage());
        assertTrue(ex.getMessage().contains("5001"), ex.getMessage());
    }

    @Test
    @DisplayName("找不到匹配的补贴标准 → 明确报错")
    void noStandard() {
        when(contractMapper.selectById(2001L)).thenReturn(contract());
        when(standardMapper.selectList(any())).thenReturn(List.of());
        BizException ex = assertThrows(BizException.class,
                () -> preview(new SubsidyCalcCmd(2001L, null, null, null, null)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    @Test
    @DisplayName("合同不存在 → 404")
    void contractNotFound() {
        when(contractMapper.selectById(2001L)).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> preview(new SubsidyCalcCmd(2001L, null, null, null, null)));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    @Test
    @DisplayName("结果 explain 含计算口径（审计与前端展示需要）")
    void explainPresent() {
        givenStandard(std("FIXED", "800", null));
        var r = preview(new SubsidyCalcCmd(2001L, null, null, null, null));
        assertTrue(r.explain().contains("定额"), r.explain());
        assertEquals("FIXED", r.subsidyMode());
        assertEquals("SUB-FIXED", r.standardCode());
    }
}
