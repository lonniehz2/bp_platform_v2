package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.AlertCreateCmd;
import com.yundao.bp.ops.dto.AlertStatsVO;
import com.yundao.bp.ops.dto.AlertVO;

/**
 * 告警中心服务。
 */
public interface AlertService {

    AlertVO create(AlertCreateCmd cmd);

    AlertVO get(Long id);

    PageResult<AlertVO> page(long pageNum, long pageSize, String category, String level,
                             String status, Long orgId, String keyword);

    /** 开始处置：PENDING/ESCALATED → HANDLING。 */
    AlertVO handle(Long id, Long handleUserId, String action, String result);

    /** 办结闭环：→ HANDLED。 */
    AlertVO resolve(Long id, Long handleUserId, String result);

    /** 标为误报：→ IGNORED。 */
    AlertVO ignore(Long id, Long handleUserId, String reason);

    /** 升级：→ ESCALATED。 */
    AlertVO escalate(Long id, String reason);

    /** 告警转工单（生成 ALERT 类型工单并关联）。 */
    AlertVO toWorkOrder(Long id, Long operatorId, String operatorName);

    /** 大屏统计。 */
    AlertStatsVO stats(Long orgId);
}
