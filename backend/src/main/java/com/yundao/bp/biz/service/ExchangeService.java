package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ExchangeCreateCmd;
import com.yundao.bp.biz.dto.ExchangeVO;
import com.yundao.bp.common.api.PageResult;

/**
 * 换房服务。
 *
 * <p><b>流程</b>：申请 → 审批 → 批准 → 执行（释放原房源、启用新房源、权限迁移）。
 *
 * <p><b>政策约束</b>：
 * <ul>
 *   <li><b>成都</b>：同一租期内限换 <b>1 次</b>，第 2 次申请直接拒绝</li>
 *   <li><b>重庆</b>：应换不换（{@code no_exchange_flag=1}）按 <b>1.5 倍</b>计租，
 *       由本服务设置 {@code rent_multiplier}，供计费引擎读取</li>
 * </ul>
 */
public interface ExchangeService {

    /** 申请换房（校验成都限换 1 次）。 */
    ExchangeVO apply(ExchangeCreateCmd cmd);

    ExchangeVO get(Long id);

    PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId, Long oldContractId,
                                String status);

    /** 提交审批。 */
    ExchangeVO submit(Long id);

    /** 批准。 */
    ExchangeVO approve(Long id, String opinion);

    /** 驳回。 */
    ExchangeVO reject(Long id, String reason);

    /** 执行换房（权限迁移 + 原房源释放 + 新合同关联）。 */
    ExchangeVO complete(Long id);

    /** 标记"应换不换"（重庆：按 1.5 倍计租）。 */
    ExchangeVO markNoExchange(Long id, String reason);

    /** 统计某合同已完成的换房次数。 */
    int countCompleted(Long oldContractId);
}
