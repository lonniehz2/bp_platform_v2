# -*- coding: utf-8 -*-
"""生成 ConfigService 优先级测试 + MessageService 模板渲染测试"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp'

# ==================== 1) 系统参数优先级 ====================
CONFIG_TEST = r'''package com.yundao.bp.sys;

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
'''

# ==================== 2) 消息模板渲染 ====================
MSG_TEST = r'''package com.yundao.bp.msg;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.msg.entity.MsgTemplate;
import com.yundao.bp.msg.mapper.MsgSendRecordMapper;
import com.yundao.bp.msg.mapper.MsgSubscriptionMapper;
import com.yundao.bp.msg.mapper.MsgTemplateMapper;
import com.yundao.bp.msg.mapper.MsgTodoMapper;
import com.yundao.bp.msg.service.impl.MessageServiceImpl;
import java.util.LinkedHashMap;
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
 * 消息模板渲染测试。
 *
 * <p>模板渲染的坑集中在：变量替换遗漏、特殊字符（$ \）被当成正则、
 * 缺变量导致整条通知发不出。这些都会直接造成「通知没发到住户」。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class MessageTemplateTest {

    @Mock
    private MsgTemplateMapper templateMapper;
    @Mock
    private MsgSubscriptionMapper subMapper;
    @Mock
    private MsgSendRecordMapper recordMapper;
    @Mock
    private MsgTodoMapper todoMapper;

    private MessageServiceImpl service;

    private static MsgTemplate tpl(String content) {
        MsgTemplate t = new MsgTemplate();
        t.setTemplateCode("T1");
        t.setChannel("INNER");
        t.setContentTpl(content);
        t.setTitleTpl("标题");
        t.setTemplateStatus("ENABLED");
        return t;
    }

    private void given(String content) {
        when(templateMapper.selectOne(any())).thenReturn(tpl(content));
    }

    @BeforeEach
    void setUp() {
        service = new MessageServiceImpl(templateMapper, subMapper, recordMapper, todoMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private static Map<String, Object> vars(String... kv) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i < kv.length; i += 2) {
            m.put(kv[i], kv[i + 1]);
        }
        return m;
    }

    @Test
    @DisplayName("单变量替换")
    void singleVar() {
        given("你好 ${name}");
        assertEquals("你好 张三", service.render("T1", vars("name", "张三")));
    }

    @Test
    @DisplayName("多变量全部替换（欠费催缴真实模板）")
    void multiVars() {
        given("尊敬的${name}：您已欠缴${amount}元，逾期${days}天。");
        String out = service.render("T1", vars("name", "张三", "amount", "1500.00", "days", "35"));
        assertEquals("尊敬的张三：您已欠缴1500.00元，逾期35天。", out);
        assertFalse(out.contains("${"), "不应残留占位符");
    }

    @Test
    @DisplayName("缺变量保留占位符（不报错，宁可少信息也要发出去）")
    void missingVarKeepsPlaceholder() {
        given("你好 ${name}，金额 ${amount}");
        String out = service.render("T1", vars("name", "李四"));
        assertTrue(out.contains("李四"));
        assertTrue(out.contains("${amount}"), out);
    }

    @Test
    @DisplayName("变量值含 $ 与 \\ 不被当作正则（关键坑）")
    void specialCharsInValue() {
        given("金额：${amount}");
        // Matcher.appendReplacement 若不 quoteReplacement，$1 之类会抛异常或被吞
        String out = service.render("T1", vars("amount", "100$1\\2"));
        assertEquals("金额：100$1\\2", out);
    }

    @Test
    @DisplayName("同一变量多次出现全部替换")
    void repeatedVar() {
        given("${name}您好，${name}请缴费");
        assertEquals("张三您好，张三请缴费", service.render("T1", vars("name", "张三")));
    }

    @Test
    @DisplayName("变量为空 Map 时原样返回模板")
    void nullVars() {
        given("你好 ${name}");
        assertEquals("你好 ${name}", service.render("T1", null));
    }

    @Test
    @DisplayName("模板不存在 → 明确报错")
    void templateNotFound() {
        when(templateMapper.selectOne(any())).thenReturn(null);
        BizException ex = assertThrows(BizException.class,
                () -> service.render("NOPE", vars("name", "x")));
        assertEquals(ErrorCode.NOT_FOUND, ex.errorCode());
    }

    @Test
    @DisplayName("无 ${} 的纯文本模板原样返回")
    void plainText() {
        given("这是一条普通通知");
        assertEquals("这是一条普通通知", service.render("T1", vars("name", "张三")));
    }

    @Test
    @DisplayName("中文与英文混合变量名只替换合法标识符")
    void invalidPlaceholderIgnored() {
        given("测试 ${a-b} 与 ${ok}");
        // ${a-b} 不是合法标识符（连字符），应保持原样
        String out = service.render("T1", vars("ok", "YES"));
        assertTrue(out.contains("YES"), out);
        assertTrue(out.contains("${a-b}"), out);
    }
}
'''

for rel, src in (('sys/ConfigServiceTest.java', CONFIG_TEST),
                 ('msg/MessageTemplateTest.java', MSG_TEST)):
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(src)
    print('  + %s（%d 行）' % (rel, src.count('\n')))
