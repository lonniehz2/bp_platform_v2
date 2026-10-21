package com.yundao.bp.grant.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.grant.entity.GrantReconcileDiff;
import java.util.List;
import java.util.Map;

/**
 * 授权对账服务（★ 级要求：本地授权与 IoT 平台授权必须一致）。
 *
 * <p><b>为什么需要</b>：授权是异步下发到 IoT 平台的，网络抖动、设备离线、
 * 重试耗尽都会造成「本地显示已授权、设备上其实没有」或反之。
 * 这类不一致在住户刷不开门时才会暴露，必须主动对账。
 *
 * <p><b>差异类型</b>：
 * <ul>
 *   <li>{@code LOCAL_MISSING} 本地应有但 IoT 没有 → 住户会被拒之门外（影响最大）</li>
 *   <li>{@code IOT_EXTRA} IoT 有但本地已撤销 → 安全风险（该失效的没失效）</li>
 *   <li>{@code PERIOD_MISMATCH} 有效期不一致</li>
 *   <li>{@code VALUE_MISMATCH} 介质值不一致</li>
 * </ul>
 */
public interface ReconcileService {

    /**
     * 执行对账。
     *
     * @param lockId 只对账某台锁（为空则全部）
     * @return 对账结果统计
     */
    Map<String, Object> reconcile(String lockId);

    PageResult<GrantReconcileDiff> pageDiffs(long pageNum, long pageSize, String lockId,
                                             String diffType, String handleStatus);

    List<GrantReconcileDiff> listByHandleStatus(String handleStatus);

    /**
     * 处置单条差异。
     *
     * @param action REGRANT / REVOKE / IGNORED / MANUAL
     */
    GrantReconcileDiff handle(Long diffId, String action, String remark);

    /** 批量处置（按差异类型）。 */
    Map<String, Object> handleBatch(String diffType, String action, String remark);

    /** 未处置差异统计（看板用）。 */
    Map<String, Object> stats();
}
