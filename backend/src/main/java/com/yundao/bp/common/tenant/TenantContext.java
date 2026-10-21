package com.yundao.bp.common.tenant;

import com.alibaba.ttl.TransmittableThreadLocal;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;

/**
 * 租户上下文容器。
 *
 * <p>设计依据：{@code 02_架构与技术方案.md} §14。
 *
 * <p><b>两个关键设计</b>：
 * <ol>
 *   <li>使用 {@link TransmittableThreadLocal}（阿里 TTL）而非 JDK {@code ThreadLocal}，
 *       以便跨线程池传递（{@code @Async}、{@code CompletableFuture}、自建线程池）。</li>
 *   <li><b>上下文缺失时抛异常，绝不返回 null 或"查全租户"</b>——
 *       后者会导致灾难性的跨租户数据泄露。</li>
 * </ol>
 *
 * <p><b>使用纪律</b>：每个入口（HTTP 过滤器、MQ 消费者、IoT 回调、定时任务、开放 API）
 * 都必须在 {@code try} 中 {@link #set}，并在 {@code finally} 中 {@link #clear}，
 * 防止线程复用造成串租户。
 */
public final class TenantContext {

    private static final ThreadLocal<TenantInfo> HOLDER = new TransmittableThreadLocal<>();

    private TenantContext() {
    }

    public static void set(TenantInfo info) {
        HOLDER.set(info);
    }

    public static TenantInfo get() {
        return HOLDER.get();
    }

    /**
     * 获取当前租户ID；缺失即抛 {@link ErrorCode#TENANT_CONTEXT_MISSING}。
     *
     * <p>⚠️ 这是整个多租户方案的安全基石：<b>不允许任何调用方退化为"查全部"</b>。
     */
    public static String tenantId() {
        TenantInfo info = HOLDER.get();
        if (info == null || info.tenantId() == null || info.tenantId().isBlank()) {
            throw new BizException(ErrorCode.TENANT_CONTEXT_MISSING,
                    "租户上下文缺失，拒绝执行以避免跨租户越权");
        }
        return info.tenantId();
    }

    /** 当前用户ID；缺失返回 null（系统任务场景合法）。 */
    public static Long userId() {
        TenantInfo info = HOLDER.get();
        return info == null ? null : info.userId();
    }

    public static boolean hasTenant() {
        TenantInfo info = HOLDER.get();
        return info != null && info.tenantId() != null && !info.tenantId().isBlank();
    }

    /** 必须在 finally 中调用。 */
    public static void clear() {
        HOLDER.remove();
    }

    /**
     * 在指定租户上下文中执行（自动 set / clear），供定时任务与 MQ 消费者使用。
     */
    public static void runAs(String tenantId, Runnable action) {
        TenantInfo prev = HOLDER.get();
        try {
            set(TenantInfo.of(tenantId));
            action.run();
        } finally {
            if (prev == null) {
                clear();
            } else {
                set(prev);
            }
        }
    }
}
