package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.DunningCreateCmd;
import com.yundao.bp.fin.dto.DunningVO;
import java.time.LocalDate;
import java.util.List;

/**
 * 催缴记录服务。
 */
public interface DunningService {

    /** 登记一次催缴（自动递增催缴次数）。 */
    DunningVO create(DunningCreateCmd cmd);

    DunningVO get(Long id);

    /** 按账单查催缴历史。 */
    List<DunningVO> listByBill(Long billId);

    PageResult<DunningVO> page(long pageNum, long pageSize, Long billId, Long personId,
                               String dunningType);

    /** 扫描逾期账单，返回需要催缴的账单建议（不落库）。 */
    List<DunningSuggestion> scanNeedDunning(int minOverdueDays, int maxDunningTimes);

    /** 催缴建议。 */
    record DunningSuggestion(Long billId, String billNo, Long contractId, Long personId,
                             String payerName, java.math.BigDecimal payableAmount,
                             int overdueDays, int dunningTimes, LocalDate dueDate) {
    }
}
