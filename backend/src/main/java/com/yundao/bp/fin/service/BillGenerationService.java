package com.yundao.bp.fin.service;

import com.yundao.bp.fin.dto.GenerateBatchCmd;
import com.yundao.bp.fin.dto.GenerateBatchVO;
import com.yundao.bp.fin.dto.GenerateBillsCmd;
import com.yundao.bp.fin.dto.GenerateResultVO;
import com.yundao.bp.fin.dto.RecalcBillsCmd;
import com.yundao.bp.fin.dto.RecalcBillsResult;
import com.yundao.bp.fin.dto.BillExplainVO;

/**
 * 批量自动出账服务。
 *
 * <p>把"计费引擎 + 合同 + 房源"串起来：扫描生效合同 → 逐户算费 → 生成账单 → 幂等去重。
 */
public interface BillGenerationService {

    /**
     * 批量出账。
     *
     * <p><b>幂等</b>：同「合同 + 收费项目 + 账期」已存在账单时跳过，可安全重复执行。
     */
    GenerateResultVO generate(GenerateBillsCmd cmd);

    /**
     * 多项目批量出账：一次跑多个收费项目（如租金 + 物业费）。
     *
     * <p>项目间相互隔离：某项目失败不影响其它项目，结果里逐项返回。
     */
    GenerateBatchVO generateBatch(GenerateBatchCmd cmd);

    /** 历史账单按新规则重算（仅未缴且未收款的账单，dryRun 可预览）。 */
    RecalcBillsResult recalculate(RecalcBillsCmd cmd);

    /** 账单计费明细。 */
    BillExplainVO explain(Long billId);
}
