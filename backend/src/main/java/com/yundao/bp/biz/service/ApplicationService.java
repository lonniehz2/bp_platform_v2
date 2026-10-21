package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ApplicationCreateCmd;
import com.yundao.bp.biz.dto.ApplicationVO;
import com.yundao.bp.biz.dto.ReviewCmd;
import com.yundao.bp.biz.entity.BizReviewRecord;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 保障房申请与审核服务。
 *
 * <p>流程：提交 → 受理 → 审核中 →（通过 / 不通过 / 需补件）→ 补件后回到审核中 → 通过。
 */
public interface ApplicationService {

    ApplicationVO create(ApplicationCreateCmd cmd);

    ApplicationVO get(Long id);

    PageResult<ApplicationVO> page(long pageNum, long pageSize, String securityType,
                                   String status, Long orgId, String keyword, Long personId);

    /** 受理：SUBMITTED → ACCEPTED。 */
    ApplicationVO accept(Long id, Long acceptUserId);

    /** 提交审核结果（按阶段推进状态机）。 */
    ApplicationVO review(Long id, ReviewCmd cmd, Long reviewUserId, String reviewUserName);

    /** 退回补件后重新提交：SUPPLEMENT → REVIEWING。 */
    ApplicationVO resubmit(Long id);

    /** 撤回：仅未受理前允许。 */
    ApplicationVO cancel(Long id, String reason);

    /** 审核轨迹（按轮次与时间）。 */
    List<BizReviewRecord> reviewRecords(Long applicationId);
}
