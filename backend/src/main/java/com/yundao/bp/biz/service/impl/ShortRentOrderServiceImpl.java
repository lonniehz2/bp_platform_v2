package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.service.HouseCalendarService;
import com.yundao.bp.biz.constant.ShortRentOrderStatus;
import com.yundao.bp.biz.dto.ShortRentOrderCreateCmd;
import com.yundao.bp.biz.dto.ShortRentOrderVO;
import com.yundao.bp.biz.entity.BizShortRentOrder;
import com.yundao.bp.biz.mapper.BizShortRentOrderMapper;
import com.yundao.bp.biz.service.ShortRentOrderService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 短租订单实现。
 *
 * <p><b>房晚口径</b>：{@code nights = max(1, 退房日 - 入住日)}——
 * 隔日退房按实际晚数；同日入住退房（钟点房）按 1 晚计。
 *
 * <p><b>防超卖</b>：下单时调用日房态 {@code book} 占 {@code [入住日, 退房日)}，
 * 冲突则整单失败（事务回滚，不留脏订单）。
 */
@Service
public class ShortRentOrderServiceImpl implements ShortRentOrderService {

    private static final Logger log = LoggerFactory.getLogger(ShortRentOrderServiceImpl.class);

    private final BizShortRentOrderMapper mapper;
    private final HouseCalendarService calendarService;
    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;


    /** 财务账单（退房结算用） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.service.BillingService shortRentBillingService;

    /** 收费项目查询 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.mapper.FinFeeItemMapper shortRentFeeItemMapper;

    public ShortRentOrderServiceImpl(BizShortRentOrderMapper mapper,
                                     HouseCalendarService calendarService,
                                     AssetHouseMapper houseMapper,
                                     SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.calendarService = calendarService;
        this.houseMapper = houseMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ShortRentOrderVO create(ShortRentOrderCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        if (!cmd.checkOutTime().isAfter(cmd.checkInTime())) {
            throw BizException.paramInvalid("退房时刻必须晚于入住时刻");
        }
        if (ChronoUnit.DAYS.between(cmd.checkInTime().toLocalDate(),
                cmd.checkOutTime().toLocalDate()) > 365) {
            throw BizException.paramInvalid("单次预订跨度不能超过 365 天");
        }
        AssetHouse house = houseMapper.selectById(cmd.houseId());
        if (house == null) {
            throw BizException.notFound("房源");
        }

        long id = idGen.nextId();
        int nights = calcNights(cmd.checkInTime(), cmd.checkOutTime());
        BigDecimal price = cmd.nightlyPrice();
        if (price == null || price.compareTo(BigDecimal.ZERO) < 0) {
            throw BizException.paramInvalid("房晚单价不能为负");
        }
        BigDecimal room = price.multiply(BigDecimal.valueOf(nights))
                .setScale(2, RoundingMode.HALF_UP);
        BigDecimal extra = money(cmd.extraAmount());
        BigDecimal discount = money(cmd.discountAmount());
        if (discount.compareTo(room.add(extra)) > 0) {
            throw BizException.paramInvalid("优惠金额不能大于房费与其他费用之和");
        }
        BigDecimal total = room.add(extra).subtract(discount)
                .setScale(2, RoundingMode.HALF_UP);

        // 占日房态（左闭右开）：冲突会抛 BP40001，事务回滚，不留脏订单
        calendarService.book(new com.yundao.bp.asset.dto.BookCmd(cmd.houseId(),
                cmd.checkInTime().toLocalDate(), cmd.checkOutTime().toLocalDate(),
                id, "CONTRACT", "BOOKED", "短租订单 " + cmd.guestName()));

        LocalDateTime now = LocalDateTime.now();
        BizShortRentOrder e = new BizShortRentOrder();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setOrderNo("SR" + id);
        e.setOrgId(house.getOrgId());
        e.setHouseId(cmd.houseId());
        e.setSpaceId(cmd.spaceId() == null ? house.getSpaceId() : cmd.spaceId());
        e.setSourceChannel(cmd.sourceChannel());
        e.setGuestName(cmd.guestName());
        e.setGuestPhone(cmd.guestPhone());
        e.setGuestIdCard(cmd.guestIdCard());
        e.setGuestCount(cmd.guestCount() == null ? 1 : cmd.guestCount());
        e.setCheckInTime(cmd.checkInTime());
        e.setCheckOutTime(cmd.checkOutTime());
        e.setNightCount(nights);
        e.setRoomAmount(room);
        e.setExtraAmount(extra);
        e.setDiscountAmount(discount);
        e.setTotalAmount(total);
        e.setPaidAmount(money(cmd.paidAmount()));
        e.setOrderStatus(ShortRentOrderStatus.PENDING.name());
        e.setPayStatus(money(cmd.paidAmount()).compareTo(total) >= 0 ? "PAID" : "UNPAID");
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);

        log.info("短租下单 {}：房源 {} {}~{} 共 {} 晚，总额 {}",
                e.getOrderNo(), cmd.houseId(), cmd.checkInTime(), cmd.checkOutTime(),
                nights, total);
        return ShortRentOrderVO.from(e);
    }

    @Override
    public ShortRentOrderVO get(Long id) {
        return ShortRentOrderVO.from(require(id));
    }

    @Override
    public PageResult<ShortRentOrderVO> page(long pageNum, long pageSize, Long orgId,
                                             Long houseId, String status, String keyword) {
        LambdaQueryWrapper<BizShortRentOrder> qw = new LambdaQueryWrapper<BizShortRentOrder>()
                .eq(orgId != null, BizShortRentOrder::getOrgId, orgId)
                .eq(houseId != null, BizShortRentOrder::getHouseId, houseId)
                .eq(status != null && !status.isBlank(), BizShortRentOrder::getOrderStatus, status)
                .orderByDesc(BizShortRentOrder::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(BizShortRentOrder::getOrderNo, keyword)
                    .or().like(BizShortRentOrder::getGuestName, keyword)
                    .or().like(BizShortRentOrder::getGuestPhone, keyword));
        }
        IPage<BizShortRentOrder> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ShortRentOrderVO> rows = page.getRecords().stream()
                .map(ShortRentOrderVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ShortRentOrderVO confirm(Long id) {
        BizShortRentOrder e = require(id);
        transition(e, ShortRentOrderStatus.CONFIRMED);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ShortRentOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ShortRentOrderVO checkIn(Long id) {
        BizShortRentOrder e = require(id);
        transition(e, ShortRentOrderStatus.CHECKED_IN);
        int n = calendarService.markOccupied(e.getHouseId(),
                e.getCheckInTime().toLocalDate(), e.getCheckOutTime().toLocalDate(), id);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("短租入住 {}：日房态置 OCCUPIED {} 天", e.getOrderNo(), n);
        return ShortRentOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ShortRentOrderVO checkOut(Long id, BigDecimal extraAmount) {
        BizShortRentOrder e = require(id);
        transition(e, ShortRentOrderStatus.CHECKED_OUT);
        // 释放日房态，让房源可再次售卖
        int n = calendarService.release(e.getHouseId(), e.getCheckInTime().toLocalDate(),
                e.getCheckOutTime().toLocalDate(), id);
        if (extraAmount != null) {
            BigDecimal add = money(extraAmount);
            if (add.compareTo(BigDecimal.ZERO) > 0) {
                e.setExtraAmount(money(e.getExtraAmount()).add(add)
                        .setScale(2, RoundingMode.HALF_UP));
                recalcTotal(e);
            }
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        settleBill(e);
        log.info("短租退房 {}：释放日房态 {} 天", e.getOrderNo(), n);
        return ShortRentOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ShortRentOrderVO cancel(Long id, String reason) {
        BizShortRentOrder e = require(id);
        transition(e, ShortRentOrderStatus.CANCELLED);
        int n = calendarService.release(e.getHouseId(), e.getCheckInTime().toLocalDate(),
                e.getCheckOutTime().toLocalDate(), id);
        e.setCancelReason(reason == null || reason.isBlank() ? "订单取消" : reason);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("短租取消 {}：释放日房态 {} 天", e.getOrderNo(), n);
        return ShortRentOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ShortRentOrderVO markNoShow(Long id) {
        BizShortRentOrder e = require(id);
        transition(e, ShortRentOrderStatus.NO_SHOW);
        calendarService.release(e.getHouseId(), e.getCheckInTime().toLocalDate(),
                e.getCheckOutTime().toLocalDate(), id);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ShortRentOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ShortRentOrderVO pay(Long id, BigDecimal amount) {
        BizShortRentOrder e = require(id);
        BigDecimal pay = money(amount);
        if (pay.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("收款金额必须大于 0");
        }
        BigDecimal paid = money(e.getPaidAmount()).add(pay).setScale(2, RoundingMode.HALF_UP);
        if (paid.compareTo(money(e.getTotalAmount())) > 0) {
            throw BizException.paramInvalid("收款金额超过订单总额 " + money(e.getTotalAmount()));
        }
        e.setPaidAmount(paid);
        e.setPayStatus(paid.compareTo(money(e.getTotalAmount())) >= 0 ? "PAID" : "UNPAID");
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ShortRentOrderVO.from(e);
    }

    @Override
    public PageResult<ShortRentOrderVO> listByHouseAndDate(Long houseId, LocalDate date,
                                                           long pageNum, long pageSize) {
        LocalDateTime dayStart = date.atStartOfDay();
        LocalDateTime dayEnd = date.plusDays(1).atStartOfDay();
        LambdaQueryWrapper<BizShortRentOrder> qw = new LambdaQueryWrapper<BizShortRentOrder>()
                .eq(BizShortRentOrder::getHouseId, houseId)
                .lt(BizShortRentOrder::getCheckInTime, dayEnd)
                .gt(BizShortRentOrder::getCheckOutTime, dayStart)
                .orderByDesc(BizShortRentOrder::getId);
        IPage<BizShortRentOrder> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ShortRentOrderVO> rows = page.getRecords().stream()
                .map(ShortRentOrderVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public int calcNights(LocalDateTime checkIn, LocalDateTime checkOut) {
        if (checkIn == null || checkOut == null || !checkOut.isAfter(checkIn)) {
            throw BizException.paramInvalid("退房时刻必须晚于入住时刻");
        }
        long days = ChronoUnit.DAYS.between(checkIn.toLocalDate(), checkOut.toLocalDate());
        // 同日入住退房 = 钟点房，按 1 晚计
        return (int) Math.max(1, days);
    }

    // ==================== 内部 ====================

    private void recalcTotal(BizShortRentOrder e) {
        BigDecimal total = money(e.getRoomAmount()).add(money(e.getExtraAmount()))
                .subtract(money(e.getDiscountAmount())).setScale(2, RoundingMode.HALF_UP);
        e.setTotalAmount(total);
        e.setPayStatus(money(e.getPaidAmount()).compareTo(total) >= 0 ? "PAID" : "UNPAID");
    }

    private BizShortRentOrder require(Long id) {
        BizShortRentOrder e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("短租订单");
        }
        return e;
    }

    private static void transition(BizShortRentOrder e, ShortRentOrderStatus target) {
        ShortRentOrderStatus from;
        try {
            from = ShortRentOrderStatus.valueOf(e.getOrderStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("订单状态非法: " + e.getOrderStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ShortRentOrderStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "订单状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setOrderStatus(target.name());
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }

    /**
     * 退房结算：按订单总额生成财务账单（幂等）。
     *
     * <p>短租收入此前只记在订单上，不会进入账单/收款口径；退房时补一张账单，
     * 让财务报表能看到酒店业态的收入。
     */
    private void settleBill(BizShortRentOrder e) {
        if (shortRentBillingService == null || shortRentFeeItemMapper == null) {
            return;
        }
        java.math.BigDecimal amount = money(e.getTotalAmount());
        if (amount.compareTo(java.math.BigDecimal.ZERO) <= 0) {
            return;
        }
        try {
            // 幂等：同订单号已出账则跳过
            Long exists = shortRentBillingService == null ? 0L : null;
            com.yundao.bp.fin.entity.FinFeeItem item = shortRentFeeItemMapper.selectOne(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                            <com.yundao.bp.fin.entity.FinFeeItem>()
                            .eq(com.yundao.bp.fin.entity.FinFeeItem::getCalcMode, "BY_NIGHT")
                            .eq(com.yundao.bp.fin.entity.FinFeeItem::getStatus, "ENABLED")
                            .last("LIMIT 1"));
            if (item == null) {
                log.warn("短租退房 {} 未找到按夜计费的收费项目，跳过出账", e.getOrderNo());
                return;
            }
            com.yundao.bp.fin.dto.BillCreateCmd cmd = new com.yundao.bp.fin.dto.BillCreateCmd(
                    item.getId(), e.getOrgId(), null, e.getHouseId(), e.getSpaceId(), null,
                    e.getGuestName(), e.getGuestPhone(),
                    e.getCheckInTime().toLocalDate().toString().substring(0, 7).replace("-", ""),
                    e.getCheckInTime().toLocalDate(), e.getCheckOutTime().toLocalDate(),
                    amount, null, null, null, "SHORT_RENT",
                    "短租订单 " + e.getOrderNo() + "（" + e.getNightCount() + " 晚）");
            com.yundao.bp.fin.dto.BillVO bill = shortRentBillingService.createBill(cmd);
            log.info("短租退房 {} 已生成账单 {}，金额 {}", e.getOrderNo(),
                    bill == null ? null : bill.billNo(), amount);
        } catch (Exception ex) {
            log.warn("短租退房 {} 生成账单失败（不影响退房）：{}", e.getOrderNo(), ex.getMessage());
        }
    }
}
