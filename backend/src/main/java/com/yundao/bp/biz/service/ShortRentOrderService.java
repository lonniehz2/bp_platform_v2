package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.ShortRentOrderCreateCmd;
import com.yundao.bp.biz.dto.ShortRentOrderVO;
import com.yundao.bp.common.api.PageResult;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 短租订单服务（酒店 / 民宿 / 网约房）。
 *
 * <p><b>与长租的区别</b>：
 * <ul>
 *   <li>租期<b>时刻级</b>（入住 14:00、退房次日 12:00），不是日期级</li>
 *   <li>按<b>房晚</b>计价，不是按月</li>
 *   <li>网约房需<b>实名登记</b>（住客姓名必填，证件号加密存）</li>
 * </ul>
 *
 * <p><b>与日房态联动</b>：下单即占 {@code [入住日, 退房日)}；入住置 OCCUPIED；
 * 退房/取消释放回 AVAILABLE。
 */
public interface ShortRentOrderService {

    /** 下单（自动占日房态，冲突则拒绝）。 */
    ShortRentOrderVO create(ShortRentOrderCreateCmd cmd);

    ShortRentOrderVO get(Long id);

    PageResult<ShortRentOrderVO> page(long pageNum, long pageSize, Long orgId, Long houseId,
                                      String status, String keyword);

    /** 确认订单。 */
    ShortRentOrderVO confirm(Long id);

    /** 办理入住（日房态 BOOKED → OCCUPIED）。 */
    ShortRentOrderVO checkIn(Long id);

    /** 办理退房（释放日房态，订单置已退房）。 */
    ShortRentOrderVO checkOut(Long id, BigDecimal extraAmount);

    /** 取消订单（释放日房态）。 */
    ShortRentOrderVO cancel(Long id, String reason);

    /** 标记未到（释放日房态）。 */
    ShortRentOrderVO markNoShow(Long id);

    /** 收款登记。 */
    ShortRentOrderVO pay(Long id, BigDecimal amount);

    /** 某房源某日期的订单（日房态视图用）。 */
    PageResult<ShortRentOrderVO> listByHouseAndDate(Long houseId, LocalDate date,
                                                    long pageNum, long pageSize);

    /** 计算房晚数（供前端预览）。 */
    int calcNights(LocalDateTime checkIn, LocalDateTime checkOut);
}
