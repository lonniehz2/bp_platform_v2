package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ChangeCreateCmd;
import com.yundao.bp.biz.dto.ChangeVO;
import com.yundao.bp.common.api.PageResult;
import java.math.BigDecimal;

/**
 * 合同变更服务。
 *
 * <p>⭐ <b>核心价值</b>：年审结论「调整租金」只有通过本服务才能<b>真正写回合同</b>，
 * 否则年审只是写了一段文字。
 *
 * <p><b>流程</b>：发起变更 → 审批 → 批准后<b>写回合同</b>（月租金/止租日/承租人），
 * 变更前后字段存 JSON 以便审计。
 */
public interface ContractChangeService {

    /** 发起变更（记录变更前后快照）。 */
    ChangeVO create(Long contractId, ChangeCreateCmd cmd);

    ChangeVO get(Long id);

    PageResult<ChangeVO> page(long pageNum, long pageSize, Long contractId, String changeType,
                              String status);

    /**
     * 批准并生效。
     *
     * <p>会把新值<b>写回合同</b>；租金调整会同步更新计费基准（后续出账用新租金）。
     */
    ChangeVO approve(Long id);

    ChangeVO reject(Long id, String reason);

    /**
     * 从年审结论发起调租变更（年审「ADJUST」的落地入口）。
     *
     * @param reviewId      年审单 ID
     * @param newMonthlyRent 新租金
     */
    ChangeVO createFromReview(Long reviewId, BigDecimal newMonthlyRent, String reason);
}
