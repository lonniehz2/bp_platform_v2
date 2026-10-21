# -*- coding: utf-8 -*-
"""生成实名校验接入测试（证明真的拦得住）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'

SRC = r'''package com.yundao.bp.biz;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.biz.dto.ApplicationCreateCmd;
import com.yundao.bp.biz.dto.ApplicationVO;
import com.yundao.bp.biz.entity.BizApplication;
import com.yundao.bp.biz.mapper.BizApplicationMapper;
import com.yundao.bp.biz.mapper.BizReviewRecordMapper;
import com.yundao.bp.biz.service.impl.ApplicationServiceImpl;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.person.service.VerifyRecordService;
import com.yundao.bp.sys.service.ConfigService;
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
import org.springframework.test.util.ReflectionTestUtils;

/**
 * 实名认证接入申请校验测试。
 *
 * <p><b>为什么单独测这个</b>：本项目已经出现过 3 次「接口提供了但没接入」的问题
 * （公示校验、信用校验都曾如此）。所以校验写完后<b>必须证明它真的会拦住</b>，
 * 而不是只在 Service 里躺着没人调用。
 *
 * <p>本测试直接调用 {@code ApplicationServiceImpl#create}，
 * 断言未认证时<b>申请被拒</b>、已认证时<b>申请成功</b>。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ApplicationVerifyGateTest {

    @Mock
    private BizApplicationMapper appMapper;
    @Mock
    private BizReviewRecordMapper reviewMapper;
    @Mock
    private VerifyRecordService verifyRecordService;
    @Mock
    private ConfigService configService;

    private ApplicationServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new ApplicationServiceImpl(appMapper, reviewMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(appMapper.insert(any(BizApplication.class))).thenReturn(1);
        // 默认：要求实名
        when(configService.getBool(any(), any(Boolean.class)))
                .thenAnswer(inv -> inv.getArgument(1));
        ReflectionTestUtils.setField(service, "verifyRecordService", verifyRecordService);
        ReflectionTestUtils.setField(service, "configService", configService);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    /** 构造合法申请（承诺书与授权都签了，只剩实名校验这一关）。 */
    private static ApplicationCreateCmd cmd(long personId) {
        return new ApplicationCreateCmd(personId, "PUBLIC", 1L, null, null, null, null,
                null, null, null, 1, 1, null, null, null, null);
    }

    private void givenVerify(Boolean verified) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("personId", 4001L);
        m.put("hasRecord", true);
        m.put("verified", verified);
        m.put("conclusion", Boolean.TRUE.equals(verified)
                ? "实名认证已通过（FACE_COMPARE）"
                : "最近一次认证未通过：人脸比对判定为不同人（疑似冒用身份），需重新认证");
        when(verifyRecordService.conclusion(any())).thenReturn(m);
    }

    // ==================== ⭐ 核心：拦不拦得住 ====================

    @Test
    @DisplayName("⭐⭐ 未通过实名认证 → 申请被拒")
    void rejectUnverified() {
        givenVerify(false);
        BizException ex = assertThrows(BizException.class, () -> service.create(cmd(4001L)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("实名认证"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐⭐ 拒绝信息包含失败原因，指导用户下一步操作")
    void rejectMessageActionable() {
        givenVerify(false);
        BizException ex = assertThrows(BizException.class, () -> service.create(cmd(4001L)));
        String msg = ex.getMessage();
        assertTrue(msg.contains("疑似冒用"), "应带上具体失败原因：" + msg);
        assertTrue(msg.contains("实名认证"), "应指引去哪里认证：" + msg);
    }

    @Test
    @DisplayName("⭐⭐ 已通过实名认证 → 申请成功")
    void allowVerified() {
        givenVerify(true);
        ApplicationVO vo = service.create(cmd(4001L));
        assertNotNull(vo);
        assertEquals("SUBMITTED", vo.applicationStatus() == null
                ? "SUBMITTED" : vo.applicationStatus());
    }

    @Test
    @DisplayName("⭐ 无认证记录 → 同样被拒（不是默认放行）")
    void rejectNoRecord() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("hasRecord", false);
        m.put("verified", false);
        m.put("conclusion", "无认证记录，不可进入资格审核");
        when(verifyRecordService.conclusion(any())).thenReturn(m);
        BizException ex = assertThrows(BizException.class, () -> service.create(cmd(4001L)));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
    }

    // ==================== 可配置开关 ====================

    @Test
    @DisplayName("⭐ 关闭实名开关后允许申请（部分地区先申请后认证）")
    void allowWhenDisabled() {
        when(configService.getBool(any(), any(Boolean.class))).thenReturn(false);
        givenVerify(false);
        assertNotNull(service.create(cmd(4001L)),
                "开关关闭时不应拦截");
    }

    @Test
    @DisplayName("⭐ 认证服务未部署时放行（灰度环境，不阻断业务）")
    void allowWhenServiceMissing() {
        ReflectionTestUtils.setField(service, "verifyRecordService", null);
        assertNotNull(service.create(cmd(4001L)));
    }

    @Test
    @DisplayName("⭐ 申请人缺失 → 拒绝（不能跳过校验）")
    void rejectNullPerson() {
        assertThrows(BizException.class, () -> service.create(cmd(null)));
    }

    // ==================== 校验顺序 ====================

    @Test
    @DisplayName("⭐⭐ 实名校验在承诺书之前（先告知不能申请，再让填材料）")
    void verifyCheckedBeforeCommitment() {
        givenVerify(false);
        // 承诺书也没签，但因为未认证应优先报实名错误
        ApplicationCreateCmd bad = new ApplicationCreateCmd(4001L, "PUBLIC", 1L, null,
                null, null, null, null, null, null, 0, 0, null, null, null, null);
        BizException ex = assertThrows(BizException.class, () -> service.create(bad));
        assertTrue(ex.getMessage().contains("实名认证"),
                "应优先提示实名问题，实际：" + ex.getMessage());
    }
}
'''

p = os.path.join(BASE, 'ApplicationVerifyGateTest.java')
os.makedirs(BASE, exist_ok=True)
io.open(p, 'w', encoding='utf-8').write(SRC)
print('  + biz/ApplicationVerifyGateTest.java（%d 行）' % SRC.count('\n'))
