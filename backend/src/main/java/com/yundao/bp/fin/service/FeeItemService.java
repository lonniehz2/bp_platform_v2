package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.BillingRuleCreateCmd;
import com.yundao.bp.fin.dto.CalcPreviewCmd;
import com.yundao.bp.fin.dto.FeeItemCreateCmd;
import com.yundao.bp.fin.dto.FeeItemVO;
import com.yundao.bp.fin.entity.FinBillingRule;
import java.util.List;

/**
 * 收费项目与计费规则服务。
 */
public interface FeeItemService {

    FeeItemVO createFeeItem(FeeItemCreateCmd cmd);

    FeeItemVO getFeeItem(Long id);

    PageResult<FeeItemVO> pageFeeItems(long pageNum, long pageSize, String itemType,
                                       String calcMode, String keyword);

    /** 启用/停用收费项目。 */
    FeeItemVO setFeeItemStatus(Long id, boolean enabled);

    FinBillingRule createRule(BillingRuleCreateCmd cmd);

    FinBillingRule getRule(Long id);

    List<FinBillingRule> listRules(Long feeItemId, String houseType);

    /** 政府限价审批通过（租金定价管控）。 */
    FinBillingRule approveRule(Long id, Long approveById);

    /** 试算：给定收费项目 + 上下文（可指定规则），返回金额与计算过程。 */
    BillingCalculator.Result preview(CalcPreviewCmd cmd);
}
