package com.yundao.bp.sys;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.sys.entity.SysConfig;
import com.yundao.bp.sys.mapper.SysConfigMapper;
import com.yundao.bp.sys.service.impl.ConfigServiceImpl;
import java.math.BigDecimal;
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
 * 系统参数优先级测试。
 *
 * <p>参数决定政策口径（公示天数、禁申年限等），取错值会直接导致合规判断出错，
 * 因此「本租户 &gt; 全局 &gt; 默认值」的优先级必须锁死。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ConfigServiceTest {

    @Mock
    private SysConfigMapper mapper;

    private ConfigServiceImpl service;

    private static SysConfig cfg(String tenantId, String key, String value) {
        SysConfig c = new SysConfig();
        c.setTenantId(tenantId);
        c.setConfigKey(key);
        c.setConfigValue(value);
        return c;
    }

    @BeforeEach
    void setUp() {
        service = new ConfigServiceImpl(mapper, new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    @Test
    @DisplayName("本租户配置覆盖全局配置")
    void tenantOverridesGlobal() {
        // 本租户查询返回 10；全局查询不会被调用
        when(mapper.selectOne(any())).thenReturn(cfg("350600", "biz.demo", "10"));
        assertEquals(10, service.getInt("biz.demo", 7));
    }

    @Test
    @DisplayName("本租户无配置时回退全局配置")
    void fallbackToGlobal() {
        // 第一次（本租户）返回 null，第二次（全局）返回全局值
        when(mapper.selectOne(any()))
                .thenReturn(null)
                .thenReturn(cfg(null, "biz.demo", "5"));
        assertEquals(5, service.getInt("biz.demo", 7));
    }

    @Test
    @DisplayName("都无配置时回退调用方默认值")
    void fallbackToDefault() {
        when(mapper.selectOne(any())).thenReturn(null);
        assertEquals(7, service.getInt("biz.demo", 7));
        assertEquals("x", service.getString("biz.demo", "x"));
        assertTrue(service.getBool("biz.demo", true));
    }

    @Test
    @DisplayName("参数值非法时回退默认值（不因配置错导致业务中断）")
    void invalidValueFallsBack() {
        when(mapper.selectOne(any())).thenReturn(cfg(null, "biz.demo", "not-a-number"));
        assertEquals(7, service.getInt("biz.demo", 7), "非法整型应回退默认值");
    }

    @Test
    @DisplayName("小数参数正确解析：过渡期倍率 1.5")
    void decimalParse() {
        when(mapper.selectOne(any())).thenReturn(cfg(null, "biz.termination.mult", "1.5"));
        BigDecimal v = service.getDecimal("biz.termination.mult", BigDecimal.ONE);
        assertEquals(0, new BigDecimal("1.5").compareTo(v));
    }

    @Test
    @DisplayName("布尔参数支持 true/1/Y 多种写法")
    void boolVariants() {
        when(mapper.selectOne(any())).thenReturn(cfg(null, "biz.flag", "1"));
        assertTrue(service.getBool("biz.flag", false));
        when(mapper.selectOne(any())).thenReturn(cfg(null, "biz.flag", "Y"));
        assertTrue(service.getBool("biz.flag", false));
        when(mapper.selectOne(any())).thenReturn(cfg(null, "biz.flag", "false"));
        assertFalse(service.getBool("biz.flag", true));
    }

    @Test
    @DisplayName("空值参数回退默认值")
    void blankValue() {
        when(mapper.selectOne(any())).thenReturn(cfg(null, "biz.demo", "  "));
        assertEquals(7, service.getInt("biz.demo", 7));
    }
}
