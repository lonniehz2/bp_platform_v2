package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.ComplaintCreateCmd;
import com.yundao.bp.ops.dto.ComplaintVO;

/**
 * 投诉建议服务。
 */
public interface ComplaintService {

    ComplaintVO create(ComplaintCreateCmd cmd);

    ComplaintVO get(Long id);

    PageResult<ComplaintVO> page(long pageNum, long pageSize, String type, String status,
                                 Long orgId, String keyword);

    /** 开始处理：PENDING → HANDLING。 */
    ComplaintVO handle(Long id, Long handleUserId);

    /** 处理完成：→ HANDLED。 */
    ComplaintVO resolve(Long id, Long handleUserId, String result);

    /** 归档：HANDLED → CLOSED。 */
    ComplaintVO close(Long id, Long handleUserId);

    /** 回访评价（满意度 1-5）。 */
    ComplaintVO evaluate(Long id, Integer satisfaction);

    /** 转工单（投诉升级为维修/处置工单）。 */
    ComplaintVO toWorkOrder(Long id, Long operatorId, String operatorName);
}
