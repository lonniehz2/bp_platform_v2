package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.ArrearsActionCreateCmd;
import com.yundao.bp.fin.dto.ArrearsActionVO;
import java.util.List;

/**
 * 欠费停权处置服务。
 *
 * <p><b>业务链</b>：账单逾期 → 生成处置单（通知/冻结）→ 执行（联动授权回收）→ 缴清 → 解冻。
 *
 * <p><b>安全底线（决策 D19）</b>：欠费停权<b>不得停用大门门禁</b>，
 * 默认冻结范围为 {@code EXCLUDE_MAIN_DOOR}。使用 {@code ALL} 需显式确认风险。
 */
public interface ArrearsActionService {

    /** 创建处置单（不做实际冻结）。 */
    ArrearsActionVO create(ArrearsActionCreateCmd cmd);

    ArrearsActionVO get(Long id);

    PageResult<ArrearsActionVO> page(long pageNum, long pageSize, Long contractId,
                                     Long personId, String actionType, String status);

    /** 按合同列出处置记录（含历史）。 */
    List<ArrearsActionVO> listByContract(Long contractId);

    /**
     * 执行处置单。
     *
     * <p>冻结类会联动授权模块撤销该合同空间下的生效权益（保留大门权限）。
     * 通知/限制类仅标记执行。
     */
    ArrearsActionVO execute(Long id);

    /** 撤销处置（如已缴清），冻结类会自动尝试恢复授权。 */
    ArrearsActionVO revoke(Long id, String reason);

    /** 扫描逾期账单，按合同汇总欠费，返回可处置建议（不落库）。 */
    List<ArrearsSuggestion> scanArrears(int minOverdueDays);

    /** 扫描结果。 */
    record ArrearsSuggestion(Long contractId, Long personId, Long orgId,
                             java.math.BigDecimal arrearsAmount, int overdueDays,
                             int billCount, boolean freezeRecommended) {
    }
}
