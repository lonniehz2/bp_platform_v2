package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.BillCreateCmd;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.PaymentCreateCmd;
import com.yundao.bp.fin.dto.PaymentVO;
import java.math.BigDecimal;

/**
 * 账单与收款服务（BC-08 资金账务）。
 *
 * <p><b>核销闭环</b>：账单(应收) → 收款单(实收) → 核销明细 → 账单状态与应付金额回写。
 */
public interface BillingService {

    // ---------- 账单 ----------
    BillVO createBill(BillCreateCmd cmd);

    BillVO getBill(Long id);

    PageResult<BillVO> pageBills(long pageNum, long pageSize, Long orgId, Long contractId, Long personId, Long houseId,
                                 String status, String keyword);

    /** 逾期扫描：过缴费截止日仍未缴的账单置 OVERDUE 并回填逾期天数。 */
    int scanOverdue();

    /** 减免/免除账单。 */
    BillVO waiveBill(Long id, BigDecimal waiveAmount, String reason);

    /** 作废账单（已收金额必须为 0）。 */
    BillVO cancelBill(Long id, String reason);

    // ---------- 收款 ----------
    PaymentVO createPayment(PaymentCreateCmd cmd);

    PaymentVO getPayment(Long id);

    PageResult<PaymentVO> pagePayments(long pageNum, long pageSize, Long orgId, Long personId,
                                       String status, String keyword);

    /** 确认收款成功（PENDING → SUCCESS）。 */
    PaymentVO confirmPayment(Long id);

    /**
     * 核销：把收款单的钱核到指定账单上。
     *
     * <p>核销额不能超过「收款单可核销余额」与「账单应付金额」两者较小值。
     */
    BillVO allocate(Long paymentId, Long billId, BigDecimal amount);

    /** 同一合同多张账单合并核销；跨合同拒绝。 */
    java.util.List<BillVO> allocateBatch(Long paymentId, java.util.List<AllocateItem> items);

    record AllocateItem(Long billId, BigDecimal amount) {
    }

    /** 公摊费用分摊出账。 */
    java.util.Map<String, Object> generateSharedBills(
            com.yundao.bp.fin.dto.SharedBillCmd cmd);

    /** 按账期（yyyy-MM）取账单，供趋势统计。 */
    java.util.List<com.yundao.bp.fin.entity.FinBill> listByPeriod(String period);

    /** 按账期统计催缴动作数（趋势用）。 */
    long countArrearsActions(String period);
}
