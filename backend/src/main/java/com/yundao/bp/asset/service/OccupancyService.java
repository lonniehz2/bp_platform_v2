package com.yundao.bp.asset.service;

import java.time.LocalDate;

/**
 * 房源占用服务：把「合同状态变化」翻译成「房源被占/释放」。
 *
 * <p>为什么单独抽出：房源状态和占用流水必须与合同变更**同事务**，
 * 否则会出现「合同已生效但房源还显示空置」这类可以重复配租的脏状态。
 *
 * <p>所有方法都是幂等的：重复调用不会产生重复占用记录。
 */
public interface OccupancyService {

    /**
     * 合同生效：占房。
     *
     * @param contractId 合同 ID（幂等键）
     * @param houseId    房源 ID
     * @param spaceId    房源所在空间 ID（可为空，为空时取房源的 space_id）
     * @param personId   承租人 ID
     * @param start      起租日
     * @param end        止租日
     */
    void occupyByContract(Long contractId, Long houseId, Long spaceId, Long personId,
                          LocalDate start, LocalDate end);

    /**
     * 合同终止/到期/作废：释放占用，房源回到空置（若已无其他在用占用）。
     */
    void releaseByContract(Long contractId, LocalDate actualEnd);

    /**
     * 合同续签：延长占用结束日。
     */
    void extendByContract(Long contractId, LocalDate newEnd);
}
