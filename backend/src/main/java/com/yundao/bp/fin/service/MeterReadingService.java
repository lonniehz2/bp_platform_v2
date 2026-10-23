package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.MeterReadingCmd;
import com.yundao.bp.fin.entity.FinMeterReading;

/** 能耗抄表。 */
public interface MeterReadingService {

    FinMeterReading record(MeterReadingCmd cmd);

    PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId, Long feeItemId);

    /** 按读数生成账单。 */
    BillVO bill(Long readingId);

    /** 能耗分析：月度用量/金额 + 楼栋与房源排名。 */
    java.util.Map<String, Object> analytics(Long orgId, int months);
}
