# -*- coding: utf-8 -*-
"""生成短租订单（第二部分：服务/控制器 + 日房态 markOccupied）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ---- 给 HouseCalendarService 增加 markOccupied（入住时 BOOKED -> OCCUPIED）----
p1 = os.path.join(BASE, r'asset\service\HouseCalendarService.java')
s1 = io.open(p1, encoding='utf-8').read()
if 'markOccupied' not in s1:
    s1 = s1.replace(
        '    /** 释放占用（按 bookingId 匹配，避免误放他人）。返回释放天数。 */',
        '''    /**
     * 把已预订的日期置为"已入住"（BOOKED → OCCUPIED）。
     *
     * <p>只更新处于 BOOKED 且 bookingId 匹配的日期；返回更新天数。
     */
    int markOccupied(Long houseId, LocalDate checkIn, LocalDate checkOut, Long bookingId);

    /** 释放占用（按 bookingId 匹配，避免误放他人）。返回释放天数。 */''', 1)
    io.open(p1, 'w', encoding='utf-8').write(s1)
    print('  ~ HouseCalendarService 增加 markOccupied')

p2 = os.path.join(BASE, r'asset\service\impl\HouseCalendarServiceImpl.java')
s2 = io.open(p2, encoding='utf-8').read()
if 'markOccupied' not in s2:
    method = '''    @Override
    @Transactional(rollbackFor = Exception.class)
    public int markOccupied(Long houseId, LocalDate checkIn, LocalDate checkOut,
                            Long bookingId) {
        validateRange(checkIn, checkOut, false);
        LocalDate last = checkOut.minusDays(1);
        List<AssetHouseCalendar> rows = loadRows(houseId, checkIn, last);
        int n = 0;
        LocalDateTime now = LocalDateTime.now();
        for (AssetHouseCalendar r : rows) {
            if (parseStatus(r) != DayStatus.BOOKED) {
                continue;
            }
            if (bookingId != null && r.getBookingId() != null
                    && !bookingId.equals(r.getBookingId())) {
                continue;
            }
            r.setDayStatus(DayStatus.OCCUPIED.name());
            r.setUpdateTime(now);
            calMapper.updateById(r);
            n++;
        }
        return n;
    }

'''
    anchor = '''    @Override
    @Transactional(rollbackFor = Exception.class)
    public int release(Long houseId, LocalDate checkIn, LocalDate checkOut, Long bookingId) {'''
    assert anchor in s2
    s2 = s2.replace(anchor, method + anchor, 1)
    io.open(p2, 'w', encoding='utf-8').write(s2)
    print('  ~ HouseCalendarServiceImpl 增加 markOccupied')

# ---- 服务接口 ----
FILES['biz/service/ShortRentOrderService.java'] = '''package com.yundao.bp.biz.service;

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
'''

FILES['biz/service/impl/ShortRentOrderServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

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
}
'''

FILES['biz/controller/ShortRentOrderController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.ShortRentOrderCreateCmd;
import com.yundao.bp.biz.dto.ShortRentOrderVO;
import com.yundao.bp.biz.service.ShortRentOrderService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 短租订单接口（BC-05，酒店/民宿/网约房）。
 *
 * <p>下单自动占日房态；入住置 OCCUPIED；退房/取消释放房源。
 */
@RestController
@RequestMapping("/api/v1/short-rent-orders")
public class ShortRentOrderController {

    private final ShortRentOrderService service;

    public ShortRentOrderController(ShortRentOrderService service) {
        this.service = service;
    }

    @PostMapping
    public R<ShortRentOrderVO> create(@Valid @RequestBody ShortRentOrderCreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @GetMapping("/{id}")
    public R<ShortRentOrderVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<ShortRentOrderVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                                @RequestParam(defaultValue = "20") long pageSize,
                                                @RequestParam(required = false) Long orgId,
                                                @RequestParam(required = false) Long houseId,
                                                @RequestParam(required = false) String status,
                                                @RequestParam(required = false) String keyword) {
        return R.ok(service.page(pageNum, pageSize, orgId, houseId, status, keyword));
    }

    /** 按房源+日期查订单（日房态视图）。 */
    @GetMapping("/by-house")
    public R<PageResult<ShortRentOrderVO>> byHouse(
            @RequestParam Long houseId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date,
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize) {
        return R.ok(service.listByHouseAndDate(houseId, date, pageNum, pageSize));
    }

    /** 房晚试算。 */
    @GetMapping("/calc-nights")
    public R<Integer> calcNights(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime checkIn,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime checkOut) {
        return R.ok(service.calcNights(checkIn, checkOut));
    }

    @PostMapping("/{id}/confirm")
    public R<ShortRentOrderVO> confirm(@PathVariable Long id) {
        return R.ok(service.confirm(id));
    }

    /** 办理入住。 */
    @PostMapping("/{id}/check-in")
    public R<ShortRentOrderVO> checkIn(@PathVariable Long id) {
        return R.ok(service.checkIn(id));
    }

    /** 办理退房（可追加超时/消费费用）。 */
    @PostMapping("/{id}/check-out")
    public R<ShortRentOrderVO> checkOut(@PathVariable Long id,
                                        @RequestBody(required = false) ExtraCmd cmd) {
        return R.ok(service.checkOut(id, cmd == null ? null : cmd.extraAmount()));
    }

    @PostMapping("/{id}/cancel")
    public R<ShortRentOrderVO> cancel(@PathVariable Long id,
                                     @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.cancel(id, cmd == null ? null : cmd.reason()));
    }

    @PostMapping("/{id}/no-show")
    public R<ShortRentOrderVO> noShow(@PathVariable Long id) {
        return R.ok(service.markNoShow(id));
    }

    @PostMapping("/{id}/pay")
    public R<ShortRentOrderVO> pay(@PathVariable Long id, @RequestBody PayCmd cmd) {
        return R.ok(service.pay(id, cmd.amount()));
    }

    public record ExtraCmd(BigDecimal extraAmount) {
    }

    public record ReasonCmd(String reason) {
    }

    public record PayCmd(BigDecimal amount) {
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('生成 %d 个文件' % count)
