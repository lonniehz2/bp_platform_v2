package com.yundao.bp.dev.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.dev.dto.AccessReportCmd;
import com.yundao.bp.dev.dto.AccessVO;
import com.yundao.bp.dev.dto.IdleStatVO;
import com.yundao.bp.dev.dto.TraceVO;
import java.time.LocalDate;
import java.util.List;

/**
 * 通行记录服务。
 *
 * <p>⭐ 支撑三项 ★ 级能力：
 * <ol>
 *   <li><b>行为轨迹</b>：按人/房源查开门时间线</li>
 *   <li><b>空置判定</b>：房源连续 N 天无开门记录 → 疑似空置</li>
 *   <li><b>异常开门</b>：挟持/试错/非授权时段，触发告警</li>
 * </ol>
 */
public interface AccessRecordService {

    /**
     * 上报开门记录（IoT 回调或拉取补齐）。
     *
     * <p><b>幂等</b>：按 {@code event_id} 去重，重复上报返回 false。
     *
     * @return true=新写入，false=重复
     */
    boolean report(AccessReportCmd cmd);

    /** 批量上报。 */
    int reportBatch(List<AccessReportCmd> cmds);

    PageResult<AccessVO> page(long pageNum, long pageSize, Long personId, Long houseId,
                              LocalDate dateFrom, LocalDate dateTo, Boolean abnormalOnly);

    /** ⭐ 行为轨迹：某人在区间的开门时间线。 */
    TraceVO traceByPerson(Long personId, LocalDate dateFrom, LocalDate dateTo);

    /** ⭐ 行为轨迹：某房源在区间的开门时间线。 */
    TraceVO traceByHouse(Long houseId, LocalDate dateFrom, LocalDate dateTo);

    /** ⭐ 空置判定：连续无开门天数 ≥ 阈值视为疑似空置。 */
    List<IdleStatVO> detectIdle(Long orgId, int idleDays);

    /** 不可信开门占比统计（考核用）。 */
    java.util.Map<String, Object> untrustedRatio(Long orgId, LocalDate dateFrom,
                                                 LocalDate dateTo);
}
