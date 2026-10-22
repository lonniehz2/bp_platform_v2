package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ContractCreateCmd;
import com.yundao.bp.biz.dto.ContractVO;
import com.yundao.bp.common.api.PageResult;
import java.time.LocalDate;

/**
 * 合同服务。
 *
 * <p>生命周期：起草 → 待签约 → 签约中 → 履约中 →（续签 / 到期 / 终止）。
 */
public interface ContractService {

    /** 起草合同（DRAFT）。 */
    ContractVO create(ContractCreateCmd cmd);

    ContractVO get(Long id);

    PageResult<ContractVO> page(long pageNum, long pageSize, String contractType,
                                String status, Long houseId, Long lesseePersonId, String keyword);

    /** 提交签约：DRAFT → PENDING_SIGN。 */
    ContractVO submitSign(Long id);

    /** 发起签署：PENDING_SIGN → SIGNING。 */
    ContractVO startSigning(Long id, String signVendor);

    /** 签署完成：SIGNING → EFFECTIVE（创建时需签，纸质/PAPER 可直接生效）。 */
    ContractVO sign(Long id, String signFileUrl, String signFlowId);

    /** 续签：EFFECTIVE → RENEWING，并修订止租日与金额。 */
    ContractVO renew(Long id, LocalDate newLeaseEnd, java.math.BigDecimal newMonthlyRent);

    /** 终止（退租）：EFFECTIVE/RENEWING → TERMINATED。 */
    ContractVO terminate(Long id, String reason);

    /** 作废：DRAFT/PENDING_SIGN/SIGNING → CANCELLED。 */
    ContractVO cancel(Long id, String reason);

    /** 到期扫描：把已过止租日的履约中合同置为 EXPIRED，返回处理条数。 */
    /** 更新合同条款（仅草稿）。 */
    ContractVO updateContract(Long id,
            com.yundao.bp.biz.controller.ContractController.ContractUpdateCmd cmd);

    int expireDue();
}
