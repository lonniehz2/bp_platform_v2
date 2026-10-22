package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.PublicityCreateCmd;
import com.yundao.bp.biz.dto.PublicityVO;
import com.yundao.bp.common.api.PageResult;
import java.time.LocalDate;

/**
 * 公示服务。
 *
 * <p>⭐ <b>合规（决策 D23）</b>：
 * <ul>
 *   <li>配租公示（ALLOCATION）公示期<b>不得少于 7 个自然日</b></li>
 *   <li>配租公示<b>未结束不得签约</b>（保证异议期）</li>
 *   <li>公示结束才能推进到下一环节</li>
 * </ul>
 */
public interface PublicityService {

    /** 创建公示（配租公示校验 7 天公示期）。 */
    PublicityVO create(PublicityCreateCmd cmd);

    PublicityVO get(Long id);

    PageResult<PublicityVO> page(long pageNum, long pageSize, String type, Long orgId,
                                 String status);

    /** 发布公示（草稿 → 已发布）。 */
    PublicityVO publish(Long id);

    /** 结束公示（已发布 → 已结束）。 */
    PublicityVO close(Long id, String remark);

    /**
     * 校验某组织/类型是否已完成合规公示。
     *
     * <p>供签约前置校验调用：返回 true 表示存在已结束的配租公示。
     */
    boolean hasCompletedAllocationPublicity(Long orgId, LocalDate referenceDate);

    /** 公示中签名单。 */
    java.util.List<com.yundao.bp.biz.dto.PublicityWinnerVO> winners(Long publicityId);
}
