package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.ReconcileCreateCmd;
import com.yundao.bp.fin.dto.ReconcileVO;
import java.time.LocalDate;

/**
 * 财务对账服务。
 */
public interface ReconcileService {

    /** 发起对账（自动汇总系统金额，计算差异）。 */
    ReconcileVO create(ReconcileCreateCmd cmd);

    ReconcileVO get(Long id);

    PageResult<ReconcileVO> page(long pageNum, long pageSize, LocalDate dateFrom, LocalDate dateTo,
                                 String reconcileType, String status);

    /** 处理差异（标记已处理）。 */
    ReconcileVO handle(Long id, String remark);
}
