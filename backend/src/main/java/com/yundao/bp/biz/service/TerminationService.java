package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.TerminationCreateCmd;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.common.api.PageResult;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 退租/腾退服务。
 *
 * <p>流程：申请 → 审批 → 批准 →（验房 → 结算 → 释放房源 → 回收授权）→ 办结。
 *
 * <p><b>政策口径</b>：
 * <ul>
 *   <li>重庆：腾退给 3 个月过渡期，期内租金 1.5 倍、期满 2.0 倍</li>
 *   <li>成都：搬迁期不超过 6 个月，承租人可指定物品处置人</li>
 *   <li>违规清退：需登记限制再申请结束日（如 5 年内不得再申请）</li>
 * </ul>
 */
public interface TerminationService {

    /** 申请退租（自动按类型带出过渡期/搬迁期政策参数）。 */
    TerminationVO apply(TerminationCreateCmd cmd);

    TerminationVO get(Long id);

    PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                   Long contractId, Long houseId, String keyword, Long orgId);

    /** 兼容旧调用：不带组织筛选。 */
    default PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                           Long contractId, Long houseId, String keyword) {
        return page(pageNum, pageSize, type, status, contractId, houseId, keyword, null);
    }

    /** 结算预览：押金/欠费/损坏/合计（不落库）。 */
    java.util.Map<String, Object> settlePreview(Long id);

    /** 提交审批：APPLYING → APPROVING。 */
    TerminationVO submit(Long id);

    /** 审批通过：APPROVING → APPROVED。 */
    TerminationVO approve(Long id, String opinion);

    /** 驳回：APPROVING → REJECTED。 */
    TerminationVO reject(Long id, String reason);

    /** 撤单：APPLYING → CANCELLED。 */
    TerminationVO cancel(Long id, String reason);

    /** 验房：记录验房结果与损坏赔偿（不合格时需重新验）。 */
    TerminationVO inspect(Long id, String inspectStatus, String inspectResult,
                          BigDecimal damageAmount, String inspectImages);

    /** 结算：押金/欠费/损坏 → 结算金额。 */
    TerminationVO settle(Long id, BigDecimal depositRefund, BigDecimal arrearsAmount);

    /** 标记房源已释放 / 授权已回收（供 house/grant 模块回调）。 */
    TerminationVO markReleased(Long id, Boolean houseReleased, Boolean grantRevoked);

    /** 办结：COMPLETED（要求四个前置齐备）。 */
    TerminationVO complete(Long id, LocalDate actualExitDate);

    /** 登记强制执行 / 公证 / 物品处置人。 */
    TerminationVO registerEnforce(Long id, LocalDate applyDate, String court,
                                 String itemHandlerName, String itemHandlerPhone,
                                 String notaryNo);
}
