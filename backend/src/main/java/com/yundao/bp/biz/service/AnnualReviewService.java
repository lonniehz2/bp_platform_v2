package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ReviewCreateCmd;
import com.yundao.bp.biz.dto.ReviewFinishCmd;
import com.yundao.bp.biz.dto.ReviewVO;
import com.yundao.bp.common.api.PageResult;
import java.util.List;

/**
 * 年审（复核）服务。
 *
 * <p><b>业务意义</b>：保障房要求保障对象每年复核收入/房产/人口变化，
 * 结果决定「保留 / 调租 / 退出」，是防止"骗保""超标占用"的核心手段。
 */
public interface AnnualReviewService {

    /** 创建复核单（幂等：同人同年度同类型仅一条）。 */
    ReviewVO create(ReviewCreateCmd cmd);

    ReviewVO get(Long id);

    PageResult<ReviewVO> page(long pageNum, long pageSize, Long personId, String reviewYear,
                              String reviewType, String status);

    /** 开始复核（待复核 → 复核中）。 */
    ReviewVO start(Long id);

    /** 完成复核（填写结果，自动推算下次复核日期）。 */
    ReviewVO finish(Long id, ReviewFinishCmd cmd);

    /**
     * 批量生成年度复核单。
     *
     * <p>扫描生效合同，为该年度未创建复核单的合同生成复核单。
     */
    BatchResult createBatch(String reviewYear, Long orgId, String reviewBatch, boolean dryRun);

    /** 将超期未完成的复核置为 OVERDUE，返回处理数。 */
    int markOverdue();

    /** 批量结果。 */
    record BatchResult(String reviewYear, int scanned, int created, int skipped,
                       boolean dryRun, List<String> skipReasons) {
    }
}
