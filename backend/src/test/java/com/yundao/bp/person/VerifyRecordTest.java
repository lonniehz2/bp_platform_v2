package com.yundao.bp.person;

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
import com.yundao.bp.person.entity.PersonVerifyRecord;
import com.yundao.bp.person.mapper.PersonVerifyRecordMapper;
import com.yundao.bp.person.service.impl.VerifyRecordServiceImpl;
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
 * 实名认证留痕测试。
 *
 * <p><b>核心是人脸结果六值语义</b>：必须区分「确认不是本人」（疑似冒用）
 * 与「照片糊了比对不了」（重传即可）。只存「通过/不通过」会把这两类混为一谈，
 * 既冤枉申请人，也放过了真正的冒用者。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class VerifyRecordTest {

    @Mock
    private PersonVerifyRecordMapper mapper;

    private VerifyRecordServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new VerifyRecordServiceImpl(mapper,
                new SnowflakeIdGenerator(1, 1),
                org.mockito.Mockito.mock(com.yundao.bp.person.mapper.PersonMapper.class));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(mapper.insert(any(PersonVerifyRecord.class))).thenReturn(1);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    private PersonVerifyRecord rec(String face, String citizen) {
        return service.record(4001L, "FACE_COMPARE", "张三", "hash", null, null,
                "CMD1", "100", "1", new BigDecimal("88.5"), face, citizen, "{}");
    }

    // ==================== ⭐⭐ 六值语义 ====================

    @Test
    @DisplayName("⭐⭐ face=1 同一人 → 通过（无论 citizen 是否为空）")
    void samePersonPasses() {
        PersonVerifyRecord r = rec("1", null);
        assertEquals(1, r.getVerifyPass());
        assertEquals(null, r.getFailReason());
    }

    @Test
    @DisplayName("⭐⭐ face=2 不同人 → 不通过，原因标注疑似冒用身份")
    void differentPersonFails() {
        PersonVerifyRecord r = rec("2", null);
        assertEquals(0, r.getVerifyPass());
        assertTrue(r.getFailReason().contains("疑似冒用"), r.getFailReason());
    }

    @Test
    @DisplayName("⭐⭐ face=3 不能确定 → 与不同人区分开（建议转人工）")
    void uncertainIsDistinct() {
        PersonVerifyRecord r = rec("3", null);
        assertEquals(0, r.getVerifyPass());
        assertTrue(r.getFailReason().contains("不能确定"), r.getFailReason());
        assertFalse(r.getFailReason().contains("冒用"), r.getFailReason());
    }

    @Test
    @DisplayName("⭐ face=4 无法比对 → 提示重传照片（不是冒用）")
    void cannotCompare() {
        PersonVerifyRecord r = rec("4", null);
        assertEquals(0, r.getVerifyPass());
        assertTrue(r.getFailReason().contains("重新上传"), r.getFailReason());
    }

    @Test
    @DisplayName("⭐ face=5 库中无照片")
    void noPhotoInLibrary() {
        PersonVerifyRecord r = rec("5", null);
        assertEquals(0, r.getVerifyPass());
        assertTrue(r.getFailReason().contains("无该照片"), r.getFailReason());
    }

    @Test
    @DisplayName("face=0/null → 未取得比对结果")
    void noResult() {
        PersonVerifyRecord r = rec("0", null);
        assertEquals(0, r.getVerifyPass());
        assertTrue(r.getFailReason().contains("未取得"), r.getFailReason());
    }

    // ==================== 身份核查 ====================

    @Test
    @DisplayName("⭐⭐ 人脸通过但身份核查不一致 → 不通过（防冒用）")
    void faceOkButCitizenMismatch() {
        PersonVerifyRecord r = rec("1", "2");
        assertEquals(0, r.getVerifyPass(), "身份核查不一致必须拦截");
        assertTrue(r.getFailReason().contains("不一致"), r.getFailReason());
    }

    @Test
    @DisplayName("⭐ 人脸通过但身份证查无此号 → 不通过")
    void faceOkButIdNotFound() {
        PersonVerifyRecord r = rec("1", "3");
        assertEquals(0, r.getVerifyPass());
        assertTrue(r.getFailReason().contains("查无此号"), r.getFailReason());
    }

    @Test
    @DisplayName("人脸通过 + 身份一致 → 通过")
    void bothOk() {
        assertEquals(1, rec("1", "1").getVerifyPass());
    }

    @Test
    @DisplayName("⭐ 人脸不通过时优先报人脸原因（不被身份核查掩盖）")
    void faceReasonTakesPriority() {
        PersonVerifyRecord r = rec("2", "2");
        assertTrue(r.getFailReason().contains("人脸"), r.getFailReason());
    }

    // ==================== 留痕内容 ====================

    @Test
    @DisplayName("⭐ 留痕包含请求号、commandId、分数、原始响应")
    void recordContainsTrace() {
        PersonVerifyRecord r = rec("1", "1");
        assertTrue(r.getRequestNo().startsWith("VR"), r.getRequestNo());
        assertEquals("CMD1", r.getCommandId());
        assertEquals(0, new BigDecimal("88.5").compareTo(r.getFaceScore()));
        assertEquals("{}", r.getRawResponse());
    }

    @Test
    @DisplayName("缺认证类型 → 拒绝")
    void requireVerifyType() {
        BizException ex = assertThrows(BizException.class,
                () -> service.record(4001L, null, "张三", null, null, null, null,
                        null, null, null, null, null, null));
        assertEquals(ErrorCode.PARAM_INVALID, ex.errorCode());
    }

    @Test
    @DisplayName("超长原始响应被截断（防止大报文打爆存储）")
    void truncateRawResponse() {
        String big = "x".repeat(5000);
        PersonVerifyRecord r = service.record(4001L, "FACE_COMPARE", null, null, null,
                null, null, null, null, null, "1", null, big);
        assertTrue(r.getRawResponse().length() < 5000,
                "实际长度 " + r.getRawResponse().length());
        assertTrue(r.getRawResponse().endsWith("(截断)"));
    }

    // ==================== 结论与统计 ====================

    @Test
    @DisplayName("⭐ 认证结论：无记录时明确不可进入资格审核")
    void conclusionNoRecord() {
        when(mapper.selectList(any())).thenReturn(List.of());
        Map<String, Object> m = service.conclusion(4001L);
        assertEquals(false, m.get("hasRecord"));
        assertEquals(false, m.get("verified"));
        assertTrue(String.valueOf(m.get("conclusion")).contains("不可进入"));
    }

    @Test
    @DisplayName("⭐ 认证结论取最近一次结果")
    void conclusionLatest() {
        PersonVerifyRecord fail = rec("2", null);
        fail.setVerifyPass(0);
        fail.setFailReason("人脸比对判定为不同人（疑似冒用身份）");
        when(mapper.selectList(any())).thenReturn(List.of(fail));
        Map<String, Object> m = service.conclusion(4001L);
        assertEquals(false, m.get("verified"));
        assertTrue(String.valueOf(m.get("conclusion")).contains("疑似冒用"),
                String.valueOf(m.get("conclusion")));
    }

    @Test
    @DisplayName("⭐ 失败原因分布统计")
    void failStats() {
        PersonVerifyRecord a = rec("2", null);
        PersonVerifyRecord b = rec("2", null);
        PersonVerifyRecord c = rec("1", "1");
        when(mapper.selectList(any())).thenReturn(List.of(a, b));
        when(mapper.selectCount(any())).thenReturn(5L);
        Map<String, Object> s = service.failStats();
        assertEquals(2, s.get("failed"));
        assertEquals(40.0, s.get("failRate"));
        assertTrue(((Map<?, ?>) s.get("byReason")).containsKey(a.getFailReason()));
    }

    @Test
    @DisplayName("判定函数抽取可独立校验（与记录逻辑一致）")
    void judgeHelper() {
        assertTrue(VerifyRecordServiceImplAccess.judge("1", "1"));
        assertFalse(VerifyRecordServiceImplAccess.judge("2", "1"));
        assertFalse(VerifyRecordServiceImplAccess.judge("1", "2"));
        assertTrue(VerifyRecordServiceImplAccess.judge("1", null));
    }

    /** 通过反射访问包级静态方法（保持实现可见性最小化）。 */
    static class VerifyRecordServiceImplAccess {
        static boolean judge(String face, String citizen) {
            try {
                var m = VerifyRecordServiceImpl.class
                        .getDeclaredMethod("judge", String.class, String.class);
                m.setAccessible(true);
                return (boolean) m.invoke(null, face, citizen);
            } catch (Exception e) {
                throw new IllegalStateException(e);
            }
        }
    }
}
