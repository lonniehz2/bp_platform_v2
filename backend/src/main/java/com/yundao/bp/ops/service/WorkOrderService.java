package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsWorkorderLog;
import java.util.List;

/**
 * 工单服务。
 *
 * <p>状态机：PENDING → ASSIGNED → ACCEPTED → PROCESSING → FINISHED → CLOSED
 * （另有 CANCELLED / REJECTED 终态）。每次流转都写 {@code bp_ops_workorder_log}。
 */
public interface WorkOrderService {

    WorkOrderVO create(WorkOrderCreateCmd cmd);

    WorkOrderVO get(Long id);

    /** 流转记录（按时间正序）。 */
    List<OpsWorkorderLog> logs(Long id);

    PageResult<WorkOrderVO> page(long pageNum, long pageSize, String orderType,
                                 String orderStatus, Long assignUserId, String keyword);

    /** 派单。 */
    WorkOrderVO assign(Long id, Long assignUserId, String assignUserName,
                       String assignUserPhone, String content);

    /** 接单（记录响应时间，并结算响应 SLA）。 */
    WorkOrderVO accept(Long id, Long operatorId, String operatorName, String content);

    /** 开始处理。 */
    WorkOrderVO start(Long id, Long operatorId, String operatorName, String content);

    /** 完工（记录完工时间，结算完工 SLA）。 */
    WorkOrderVO finish(Long id, Long operatorId, String operatorName,
                       String handleResult, String content);

    /** 闭环（记录闭环时间；考核指标）。 */
    WorkOrderVO close(Long id, Long operatorId, String operatorName, String content);

    /** 取消。 */
    WorkOrderVO cancel(Long id, Long operatorId, String operatorName, String reason);

    /** 驳回。 */
    WorkOrderVO reject(Long id, Long operatorId, String operatorName, String reason);
}
