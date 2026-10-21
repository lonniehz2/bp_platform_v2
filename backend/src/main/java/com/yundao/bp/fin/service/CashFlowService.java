package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.constant.FlowBizType;
import com.yundao.bp.fin.constant.FlowType;
import com.yundao.bp.fin.dto.CashFlowRecordCmd;
import com.yundao.bp.fin.dto.CashFlowVO;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 资金流水服务。
 *
 * <p>业务侧（收款确认、退款打款、补贴发放）通过 {@code record} 自动写入，
 * 金额带符号：收入为正、支出为负。
 */
public interface CashFlowService {

    /** 自动记流水（供业务模块调用）。 */
    CashFlowVO record(FlowType type, FlowBizType bizType, Long bizId, BigDecimal amount,
                      String remark);

    /** 手工记流水。 */
    CashFlowVO recordManual(CashFlowRecordCmd cmd);

    CashFlowVO get(Long id);

    PageResult<CashFlowVO> page(long pageNum, long pageSize, String flowType, String bizType,
                                Long bizId, LocalDate dateFrom, LocalDate dateTo);

    /** 期间净流入（收入合计 - 支出合计）。 */
    BigDecimal netAmount(LocalDate dateFrom, LocalDate dateTo);

    /** 校验流水（人工核对账实一致性）。 */
    CashFlowVO verify(Long id, String remark);
}
