package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.DepositCreateCmd;
import com.yundao.bp.fin.dto.DepositVO;
import com.yundao.bp.fin.dto.RefundCreateCmd;
import com.yundao.bp.fin.dto.RefundVO;
import java.math.BigDecimal;

/**
 * 押金台账 + 退款单服务。
 *
 * <p>退租结算落地路径：
 * <pre>
 *   押金台账(已收 2000) ──抵扣损坏 300──> 余额 1700
 *   ──申请退款 1700（DEPOSIT）──> 审批 ──> 已退款，台账 REFUNDED
 * </pre>
 */
public interface DepositRefundService {

    // ---------- 押金台账 ----------
    /** 建立押金台账（签约时调用，一合同一条）。 */
    DepositVO createDeposit(DepositCreateCmd cmd);

    DepositVO getDeposit(Long id);

    /** 按合同查押金台账。 */
    DepositVO getDepositByContract(Long contractId);

    PageResult<DepositVO> pageDeposits(long pageNum, long pageSize, Long contractId,
                                       Long personId, String status);

    /** 补收押金。 */
    DepositVO receiveDeposit(Long id, BigDecimal amount);

    /** 押金抵扣（如退租损坏赔偿）。 */
    DepositVO deductDeposit(Long id, BigDecimal amount, String reason);

    // ---------- 退款单 ----------
    RefundVO createRefund(RefundCreateCmd cmd);

    RefundVO getRefund(Long id);

    PageResult<RefundVO> pageRefunds(long pageNum, long pageSize, Long personId,
                                     Long contractId, String status);

    /** 审批通过。 */
    RefundVO approveRefund(Long id, Long approveById);

    /** 驳回。 */
    RefundVO rejectRefund(Long id, Long approveById, String reason);

    /** 打款完成（联动押金台账减少余额）。 */
    RefundVO completeRefund(Long id);
}
