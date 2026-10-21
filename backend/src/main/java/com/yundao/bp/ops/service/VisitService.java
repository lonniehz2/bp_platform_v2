package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.VisitCreateCmd;
import com.yundao.bp.ops.dto.VisitResultCmd;
import com.yundao.bp.ops.dto.VisitVO;

/**
 * 巡房/入户走访服务。
 */
public interface VisitService {

    VisitVO create(VisitCreateCmd cmd);

    VisitVO get(Long id);

    PageResult<VisitVO> page(long pageNum, long pageSize, String visitType, String visitStatus,
                             Long houseId, String keyword);

    /** 回填走访结果（PENDING → DONE/REFUSED/ABSENT/CANCELLED）。 */
    VisitVO report(Long id, VisitResultCmd cmd);

    /**
     * 走访异常转工单：发现转租/闲置/违规时生成处置工单。
     */
    VisitVO toWorkOrder(Long id, Long operatorId, String operatorName);

    /** 取消走访任务。 */
    VisitVO cancel(Long id, String reason);
}
