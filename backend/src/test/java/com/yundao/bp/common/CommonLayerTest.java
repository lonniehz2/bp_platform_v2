package com.yundao.bp.common;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * common 基础层测试。重点覆盖两条安全纪律：
 * <ol>
 *   <li><b>租户上下文缺失必须抛异常</b>（不得退化为查全租户）</li>
 *   <li><b>线程复用不得串租户</b>（clear 生效）</li>
 * </ol>
 */
class CommonLayerTest {

    @AfterEach
    void cleanup() {
        TenantContext.clear();
    }

    // ==================== 租户上下文 ====================

    @Test
    @DisplayName("上下文缺失时 tenantId() 必须抛异常（安全基石）")
    void missingTenantThrows() {
        TenantContext.clear();
        BizException ex = assertThrows(BizException.class, TenantContext::tenantId);
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING, ex.errorCode());
        assertFalse(TenantContext.hasTenant());
    }

    @Test
    @DisplayName("设置后可正确读取")
    void setAndGet() {
        TenantContext.set(TenantInfo.of("350600", 1001L));
        assertEquals("350600", TenantContext.tenantId());
        assertEquals(1001L, TenantContext.userId());
        assertTrue(TenantContext.hasTenant());
    }

    @Test
    @DisplayName("clear 后再次访问必须抛异常（线程复用不串租户）")
    void clearRemovesContext() {
        TenantContext.set(TenantInfo.of("T-A"));
        assertEquals("T-A", TenantContext.tenantId());
        TenantContext.clear();
        assertThrows(BizException.class, TenantContext::tenantId);
    }

    @Test
    @DisplayName("系统任务场景 userId 允许为 null")
    void userIdNullable() {
        TenantContext.set(TenantInfo.of("T-A"));
        assertEquals("T-A", TenantContext.tenantId());
        assertNull(TenantContext.userId());
    }

    @Test
    @DisplayName("runAs 执行后恢复原上下文")
    void runAsRestores() {
        TenantContext.set(TenantInfo.of("T-OUTER"));
        TenantContext.runAs("T-INNER", () -> assertEquals("T-INNER", TenantContext.tenantId()));
        assertEquals("T-OUTER", TenantContext.tenantId(), "runAs 结束后应恢复外层租户");
    }

    @Test
    @DisplayName("runAs 在无外层上下文时执行后应清空")
    void runAsClearsWhenNoOuter() {
        TenantContext.clear();
        TenantContext.runAs("T-X", () -> assertEquals("T-X", TenantContext.tenantId()));
        assertThrows(BizException.class, TenantContext::tenantId);
    }

    @Test
    @DisplayName("runAs 内抛异常也要恢复上下文")
    void runAsRestoresOnException() {
        TenantContext.set(TenantInfo.of("T-OUTER"));
        assertThrows(IllegalStateException.class, () ->
                TenantContext.runAs("T-INNER", () -> {
                    throw new IllegalStateException("boom");
                }));
        assertEquals("T-OUTER", TenantContext.tenantId());
    }

    @Test
    @DisplayName("TTL 继承语义：新建池线程会继承创建时的上下文（需配合 clear 防脏值）")
    void ttlInheritsOnThreadCreation() throws Exception {
        // 事实：TransmittableThreadLocal 继承自 InheritableThreadLocal，
        // 因此**线程首次创建时**会继承父线程的值。
        // 这既是便利也是风险：池化线程可能在后续无关请求中残留旧租户值，
        // 所以每个入口都必须 try{set}finally{clear}（本类 clearRemovesContext 已覆盖）。
        ExecutorService pool = Executors.newFixedThreadPool(1);
        try {
            TenantContext.set(TenantInfo.of("T-INHERIT"));
            String seen = pool.submit((Callable<String>) TenantContext::tenantId)
                    .get(5, TimeUnit.SECONDS);
            assertEquals("T-INHERIT", seen, "新建线程应继承父线程上下文");
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    @DisplayName("TtlExecutors 包装后可逐任务传递不同租户，互不干扰")
    void ttlExecutorsPropagatesPerTask() throws Exception {
        ExecutorService raw = Executors.newFixedThreadPool(1);
        ExecutorService pool = com.alibaba.ttl.threadpool.TtlExecutors.getTtlExecutorService(raw);
        try {
            List<String> seen = new ArrayList<>();
            for (String tid : List.of("T-1", "T-2", "T-3")) {
                TenantContext.set(TenantInfo.of(tid));
                seen.add(pool.submit((Callable<String>) TenantContext::tenantId)
                        .get(5, TimeUnit.SECONDS));
            }
            assertEquals(List.of("T-1", "T-2", "T-3"), seen,
                    "TtlExecutors 应按提交时刻的上下文逐任务传递");
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    @DisplayName("并发 set/clear 不产生串租户")
    void concurrentNoCrossTenant() throws Exception {
        int threads = 8;
        int rounds = 200;
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        AtomicBoolean bad = new AtomicBoolean(false);
        try {
            List<Future<?>> fs = new ArrayList<>();
            for (int t = 0; t < threads; t++) {
                final String tid = "T-" + t;
                fs.add(pool.submit(() -> {
                    for (int r = 0; r < rounds; r++) {
                        TenantContext.set(TenantInfo.of(tid));
                        if (!tid.equals(TenantContext.tenantId())) {
                            bad.set(true);
                        }
                        TenantContext.clear();
                    }
                }));
            }
            for (Future<?> f : fs) {
                f.get(20, TimeUnit.SECONDS);
            }
        } finally {
            pool.shutdownNow();
        }
        assertFalse(bad.get(), "并发场景下出现串租户");
    }

    @Test
    @DisplayName("TenantInfo 拒绝空 tenantId")
    void tenantInfoValidates() {
        assertThrows(IllegalArgumentException.class, () -> TenantInfo.of(null));
        assertThrows(IllegalArgumentException.class, () -> TenantInfo.of("  "));
    }

    // ==================== 雪花 ID ====================

    @Test
    @DisplayName("雪花 ID 单调递增且有界")
    void snowflakeMonotonic() {
        SnowflakeIdGenerator g = new SnowflakeIdGenerator(1, 1);
        long prev = -1;
        for (int i = 0; i < 5000; i++) {
            long id = g.nextId();
            assertTrue(id > prev, "ID 必须递增");
            assertTrue(id > 0, "ID 必须为正");
            prev = id;
        }
    }

    @Test
    @DisplayName("雪花 ID 并发生成不重复")
    void snowflakeUniqueConcurrent() throws Exception {
        SnowflakeIdGenerator g = new SnowflakeIdGenerator(1, 1);
        int threads = 8;
        int per = 2000;
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        List<Future<List<Long>>> fs = new ArrayList<>();
        try {
            for (int t = 0; t < threads; t++) {
                fs.add(pool.submit(() -> {
                    List<Long> ids = new ArrayList<>(per);
                    for (int i = 0; i < per; i++) {
                        ids.add(g.nextId());
                    }
                    return ids;
                }));
            }
            Set<Long> all = new HashSet<>();
            for (Future<List<Long>> f : fs) {
                all.addAll(f.get(30, TimeUnit.SECONDS));
            }
            assertEquals(threads * per, all.size(), "并发生成的 ID 出现重复");
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    @DisplayName("不同机器号的 ID 不冲突")
    void snowflakeDifferentWorker() {
        SnowflakeIdGenerator a = new SnowflakeIdGenerator(1, 1);
        SnowflakeIdGenerator b = new SnowflakeIdGenerator(1, 2);
        Set<Long> s = new HashSet<>();
        for (int i = 0; i < 1000; i++) {
            s.add(a.nextId());
            s.add(b.nextId());
        }
        assertEquals(2000, s.size());
    }

    @Test
    @DisplayName("非法机器号被拒绝")
    void snowflakeValidatesRange() {
        assertThrows(IllegalArgumentException.class, () -> new SnowflakeIdGenerator(32, 1));
        assertThrows(IllegalArgumentException.class, () -> new SnowflakeIdGenerator(1, 32));
        assertThrows(IllegalArgumentException.class, () -> new SnowflakeIdGenerator(-1, 1));
    }

    @Test
    @DisplayName("nextIdStr 返回可安全传给前端的字符串")
    void snowflakeStringForm() {
        SnowflakeIdGenerator g = new SnowflakeIdGenerator(1, 1);
        String s = g.nextIdStr();
        assertNotNull(s);
        assertTrue(Long.parseLong(s) > 0);
    }

    // ==================== 统一响应 ====================

    @Test
    @DisplayName("R.ok 与 R.fail 语义正确")
    void responseBody() {
        R<String> ok = R.ok("x");
        assertTrue(ok.success());
        assertEquals("x", ok.data());
        assertEquals(ErrorCode.SUCCESS.code(), ok.code());

        R<Void> fail = R.fail(ErrorCode.TENANT_CONTEXT_MISSING);
        assertFalse(fail.success());
        assertEquals(ErrorCode.TENANT_CONTEXT_MISSING.code(), fail.code());
        assertNull(fail.data());
    }

    @Test
    @DisplayName("错误码唯一且 HTTP 状态合理")
    void errorCodesValid() {
        Set<String> codes = new HashSet<>();
        for (ErrorCode ec : ErrorCode.values()) {
            assertTrue(codes.add(ec.code()), "错误码重复: " + ec.code());
            assertTrue(ec.httpStatus() >= 200 && ec.httpStatus() < 600);
            assertTrue(ec.code().startsWith("BP") && ec.code().length() == 7);
        }
    }
}
