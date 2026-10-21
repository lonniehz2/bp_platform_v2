# -*- coding: utf-8 -*-
"""生成 日房态与预订 模块（服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['asset/service/HouseCalendarService.java'] = '''package com.yundao.bp.asset.service;

import com.yundao.bp.asset.dto.AvailabilityVO;
import com.yundao.bp.asset.dto.BookCmd;
import com.yundao.bp.asset.dto.DayCellVO;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.List;

/**
 * 房源日房态与预订服务（短租业态支撑）。
 *
 * <p><b>核心保证</b>：同一房源同一天<b>不会</b>被两个单据占用。
 * 实现方式是"库唯一索引 + 预订前逐日检查可售"。
 */
public interface HouseCalendarService {

    /** 铺日历：把指定月份内缺失的日期补齐为 AVAILABLE（幂等）。返回新增天数。 */
    int ensureMonth(Long houseId, YearMonth month);

    /** 补齐区间内所有日期（缺失则建 AVAILABLE）。 */
    int ensureRange(Long houseId, LocalDate start, LocalDate end);

    /** 查某房源某月的月历。 */
    List<DayCellVO> getMonth(Long houseId, YearMonth month);

    /** 查询某房源在指定区间的可售情况（[checkIn, checkOut)）。 */
    AvailabilityVO availability(Long houseId, LocalDate checkIn, LocalDate checkOut);

    /** 批量查询某组织下在指定区间整段可售的房源。 */
    List<AvailabilityVO> searchAvailable(Long orgId, LocalDate checkIn, LocalDate checkOut);

    /**
     * 预订/占用（[checkIn, checkOut) 左闭右开）。
     *
     * <p>逐日校验必须为 AVAILABLE，任何一天被占用则<b>整单拒绝</b>（不产生部分占用）。
     */
    int book(BookCmd cmd);

    /** 释放占用（按 bookingId 匹配，避免误放他人）。返回释放天数。 */
    int release(Long houseId, LocalDate checkIn, LocalDate checkOut, Long bookingId);

    /** 手工设置某几日房态（停售/维修）。 */
    int setStatus(Long houseId, LocalDate start, LocalDate end, String dayStatus,
                  String remark);

    /** 手工改某一天的当日价（节假日调价）。 */
    DayCellVO setPrice(Long houseId, LocalDate date, java.math.BigDecimal price);
}
'''

FILES['asset/service/impl/HouseCalendarServiceImpl.java'] = '''package com.yundao.bp.asset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.constant.DayStatus;
import com.yundao.bp.asset.dto.AvailabilityVO;
import com.yundao.bp.asset.dto.BookCmd;
import com.yundao.bp.asset.dto.DayCellVO;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.entity.AssetHouseCalendar;
import com.yundao.bp.asset.mapper.AssetHouseCalendarMapper;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.asset.service.HouseCalendarService;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 日房态与预订实现。
 *
 * <p><b>区间口径</b>：{@code [checkIn, checkOut)} 左闭右开。
 * 11-01 入住、11-03 退房 → 占 11-01、11-02，11-03 可再售。
 *
 * <p><b>防超卖</b>：预订前逐日检查 {@code AVAILABLE}，任一日不满足整单拒绝；
 * 库上 {@code uk_tenant_house_date} 唯一索引兜底防并发重复插。
 */
@Service
public class HouseCalendarServiceImpl implements HouseCalendarService {

    private static final Logger log = LoggerFactory.getLogger(HouseCalendarServiceImpl.class);
    private static final DateTimeFormatter D = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    private final AssetHouseCalendarMapper calMapper;
    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;

    public HouseCalendarServiceImpl(AssetHouseCalendarMapper calMapper,
                                    AssetHouseMapper houseMapper,
                                    SnowflakeIdGenerator idGen) {
        this.calMapper = calMapper;
        this.houseMapper = houseMapper;
        this.idGen = idGen;
    }

    // ==================== 铺日历 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int ensureMonth(Long houseId, YearMonth month) {
        return ensureRange(houseId, month.atDay(1), month.atEndOfMonth());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int ensureRange(Long houseId, LocalDate start, LocalDate end) {
        validateRange(start, end, true);
        AssetHouse house = houseMapper.selectById(houseId);
        if (house == null) {
            throw BizException.notFound("房源");
        }
        List<AssetHouseCalendar> exist = calMapper.selectList(
                new LambdaQueryWrapper<AssetHouseCalendar>()
                        .eq(AssetHouseCalendar::getHouseId, houseId)
                        .ge(AssetHouseCalendar::getCalDate, start)
                        .le(AssetHouseCalendar::getCalDate, end));
        Map<LocalDate, AssetHouseCalendar> byDate = exist.stream()
                .collect(Collectors.toMap(AssetHouseCalendar::getCalDate, Function.identity(),
                        (a, b) -> a));

        String tenantId = TenantContext.tenantId();
        int added = 0;
        LocalDateTime now = LocalDateTime.now();
        for (LocalDate d = start; !d.isAfter(end); d = d.plusDays(1)) {
            if (byDate.containsKey(d)) {
                continue;
            }
            AssetHouseCalendar c = new AssetHouseCalendar();
            c.setId(idGen.nextId());
            c.setTenantId(tenantId);
            c.setOrgId(house.getOrgId());
            c.setHouseId(houseId);
            c.setCalDate(d);
            c.setDayStatus(DayStatus.AVAILABLE.name());
            c.setIsDeleted(0);
            c.setCreateTime(now);
            c.setUpdateTime(now);
            calMapper.insert(c);
            added++;
        }
        return added;
    }

    // ==================== 查询 ====================

    @Override
    public List<DayCellVO> getMonth(Long houseId, YearMonth month) {
        ensureMonth(houseId, month);
        return cells(houseId, month.atDay(1), month.atEndOfMonth());
    }

    @Override
    public AvailabilityVO availability(Long houseId, LocalDate checkIn, LocalDate checkOut) {
        validateRange(checkIn, checkOut, false);
        AssetHouse house = houseMapper.selectById(houseId);
        if (house == null) {
            throw BizException.notFound("房源");
        }
        LocalDate last = checkOut.minusDays(1);
        ensureRange(houseId, checkIn, last);

        List<DayCellVO> cs = cells(houseId, checkIn, last);
        int days = cs.size();
        int free = (int) cs.stream()
                .filter(c -> DayStatus.AVAILABLE.name().equals(c.dayStatus())).count();
        BigDecimal total = BigDecimal.ZERO;
        boolean allPriced = true;
        for (DayCellVO c : cs) {
            if (c.price() == null) {
                allPriced = false;
                break;
            }
            total = total.add(c.price());
        }
        return new AvailabilityVO(houseId, house.getHouseCode(), house.getHouseName(),
                days, free, free == days && days > 0,
                allPriced ? total : null, cs);
    }

    @Override
    public List<AvailabilityVO> searchAvailable(Long orgId, LocalDate checkIn,
                                                LocalDate checkOut) {
        validateRange(checkIn, checkOut, false);
        LambdaQueryWrapper<AssetHouse> hw = new LambdaQueryWrapper<AssetHouse>()
                .eq(orgId != null, AssetHouse::getOrgId, orgId)
                .orderByAsc(AssetHouse::getId);
        List<AssetHouse> houses = houseMapper.selectList(hw);
        List<AvailabilityVO> out = new ArrayList<>();
        for (AssetHouse h : houses) {
            try {
                AvailabilityVO av = availability(h.getId(), checkIn, checkOut);
                if (av.available()) {
                    out.add(av);
                }
            } catch (Exception e) {
                log.debug("房源 {} 可售检查跳过：{}", h.getId(), e.getMessage());
            }
        }
        return out;
    }

    // ==================== 预订 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int book(BookCmd cmd) {
        validateRange(cmd.checkIn(), cmd.checkOut(), false);
        DayStatus target;
        try {
            target = DayStatus.valueOf(cmd.targetStatus() == null
                    ? DayStatus.BOOKED.name() : cmd.targetStatus());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("目标房态不合法: " + cmd.targetStatus());
        }
        if (target != DayStatus.BOOKED && target != DayStatus.OCCUPIED) {
            throw BizException.paramInvalid("预订只能把房态置为 BOOKED 或 OCCUPIED");
        }

        LocalDate last = cmd.checkOut().minusDays(1);
        ensureRange(cmd.houseId(), cmd.checkIn(), last);
        List<AssetHouseCalendar> rows = loadRows(cmd.houseId(), cmd.checkIn(), last);

        // 逐日校验：任何一天不可售 → 整单拒绝（不产生部分占用）
        List<String> conflicts = new ArrayList<>();
        for (AssetHouseCalendar r : rows) {
            DayStatus st = parseStatus(r);
            if (!st.bookable()) {
                conflicts.add(r.getCalDate().format(D) + "(" + st.label() + ")");
            }
        }
        if (!conflicts.isEmpty()) {
            throw BizException.stateConflict(
                    "该日期已被占用，无法预订：" + String.join("、", conflicts));
        }

        String tenantId = TenantContext.tenantId();
        LocalDateTime now = LocalDateTime.now();
        for (AssetHouseCalendar r : rows) {
            r.setDayStatus(target.name());
            r.setBookingId(cmd.bookingId());
            r.setSourceType(cmd.sourceType() == null ? "BOOKING" : cmd.sourceType());
            if (cmd.remark() != null) {
                r.setRemark(cmd.remark());
            }
            r.setUpdateTime(now);
            calMapper.updateById(r);
        }
        log.info("房源 {} 预订 {}~{} 共 {} 天（bookingId={}）",
                cmd.houseId(), cmd.checkIn(), cmd.checkOut(), rows.size(), cmd.bookingId());
        return rows.size();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int release(Long houseId, LocalDate checkIn, LocalDate checkOut, Long bookingId) {
        validateRange(checkIn, checkOut, false);
        LocalDate last = checkOut.minusDays(1);
        List<AssetHouseCalendar> rows = loadRows(houseId, checkIn, last);
        int n = 0;
        LocalDateTime now = LocalDateTime.now();
        for (AssetHouseCalendar r : rows) {
            if (!parseStatus(r).occupied()) {
                continue;
            }
            // 指定了 bookingId 时只释放匹配的单据，避免误放他人
            if (bookingId != null && r.getBookingId() != null
                    && !bookingId.equals(r.getBookingId())) {
                continue;
            }
            r.setDayStatus(DayStatus.AVAILABLE.name());
            r.setBookingId(null);
            r.setSourceType(null);
            r.setUpdateTime(now);
            calMapper.updateById(r);
            n++;
        }
        return n;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int setStatus(Long houseId, LocalDate start, LocalDate end, String dayStatus,
                         String remark) {
        validateRange(start, end, true);
        DayStatus target;
        try {
            target = DayStatus.valueOf(dayStatus);
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("房态不合法: " + dayStatus);
        }
        if (target.occupied()) {
            throw BizException.paramInvalid("停售/维修请用 CLOSED 或 MAINTENANCE；占用请走预订接口");
        }
        ensureRange(houseId, start, end);
        List<AssetHouseCalendar> rows = loadRows(houseId, start, end);
        int n = 0;
        LocalDateTime now = LocalDateTime.now();
        for (AssetHouseCalendar r : rows) {
            r.setDayStatus(target.name());
            r.setRemark(remark);
            r.setUpdateTime(now);
            calMapper.updateById(r);
            n++;
        }
        return n;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DayCellVO setPrice(Long houseId, LocalDate date, BigDecimal price) {
        if (price != null && price.compareTo(BigDecimal.ZERO) < 0) {
            throw BizException.paramInvalid("当日价不能为负");
        }
        ensureRange(houseId, date, date);
        List<AssetHouseCalendar> rows = loadRows(houseId, date, date);
        if (rows.isEmpty()) {
            throw BizException.notFound("日房态");
        }
        AssetHouseCalendar r = rows.get(0);
        r.setPriceOverride(price);
        r.setUpdateTime(LocalDateTime.now());
        calMapper.updateById(r);
        return toCell(r);
    }

    // ==================== 内部 ====================

    private List<DayCellVO> cells(Long houseId, LocalDate start, LocalDate end) {
        return loadRows(houseId, start, end).stream().map(this::toCell).toList();
    }

    private List<AssetHouseCalendar> loadRows(Long houseId, LocalDate start, LocalDate end) {
        return calMapper.selectList(new LambdaQueryWrapper<AssetHouseCalendar>()
                .eq(AssetHouseCalendar::getHouseId, houseId)
                .ge(AssetHouseCalendar::getCalDate, start)
                .le(AssetHouseCalendar::getCalDate, end)
                .orderByAsc(AssetHouseCalendar::getCalDate));
    }

    private DayCellVO toCell(AssetHouseCalendar r) {
        DayStatus st = parseStatus(r);
        return new DayCellVO(r.getCalDate(), st.name(), st.label(), r.getPriceOverride(),
                r.getBookingId(), r.getSourceType(), r.getRemark());
    }

    private static DayStatus parseStatus(AssetHouseCalendar r) {
        try {
            return DayStatus.valueOf(r.getDayStatus());
        } catch (IllegalArgumentException e) {
            return DayStatus.AVAILABLE;
        }
    }

    private static void validateRange(LocalDate start, LocalDate end, boolean inclusiveEnd) {
        if (start == null || end == null) {
            throw BizException.paramInvalid("日期不能为空");
        }
        if (inclusiveEnd) {
            if (end.isBefore(start)) {
                throw BizException.paramInvalid("结束日不能早于开始日");
            }
        } else {
            if (!end.isAfter(start)) {
                throw BizException.paramInvalid("退房日必须晚于入住日");
            }
            if (ChronoUnit.DAYS.between(start, end) > 365) {
                throw BizException.paramInvalid("单次预订跨度不能超过 365 天");
            }
        }
    }
}
'''

FILES['asset/controller/HouseCalendarController.java'] = '''package com.yundao.bp.asset.controller;

import com.yundao.bp.asset.dto.AvailabilityVO;
import com.yundao.bp.asset.dto.BookCmd;
import com.yundao.bp.asset.dto.DayCellVO;
import com.yundao.bp.asset.service.HouseCalendarService;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 房源日房态与预订接口（BC-02，短租业态）。
 *
 * <p>区间口径统一为 <b>[入住, 退房) 左闭右开</b>。
 */
@RestController
@RequestMapping("/api/v1/house-calendar")
public class HouseCalendarController {

    private final HouseCalendarService service;

    public HouseCalendarController(HouseCalendarService service) {
        this.service = service;
    }

    /** 月历（自动补齐缺失日期）。 */
    @GetMapping("/{houseId}")
    public R<List<DayCellVO>> month(@PathVariable Long houseId,
                                    @RequestParam String month) {
        return R.ok(service.getMonth(houseId, YearMonth.parse(month)));
    }

    /** 补日历。 */
    @PostMapping("/{houseId}/ensure")
    public R<Integer> ensure(@PathVariable Long houseId, @RequestParam String month) {
        return R.ok(service.ensureMonth(houseId, YearMonth.parse(month)));
    }

    /** 单房源可售查询。 */
    @GetMapping("/{houseId}/availability")
    public R<AvailabilityVO> availability(
            @PathVariable Long houseId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate checkIn,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate checkOut) {
        return R.ok(service.availability(houseId, checkIn, checkOut));
    }

    /** 整段可售的房源列表（短租搜房）。 */
    @GetMapping("/available")
    public R<List<AvailabilityVO>> search(
            @RequestParam(required = false) Long orgId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate checkIn,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate checkOut) {
        return R.ok(service.searchAvailable(orgId, checkIn, checkOut));
    }

    /** 预订/占用。 */
    @PostMapping("/book")
    public R<Integer> book(@Valid @RequestBody BookCmd cmd) {
        return R.ok(service.book(cmd));
    }

    /** 释放占用。 */
    @PostMapping("/release")
    public R<Integer> release(@RequestBody ReleaseCmd cmd) {
        return R.ok(service.release(cmd.houseId(), cmd.checkIn(), cmd.checkOut(),
                cmd.bookingId()));
    }

    /** 停售/维修。 */
    @PostMapping("/{houseId}/status")
    public R<Integer> setStatus(@PathVariable Long houseId, @RequestBody StatusCmd cmd) {
        return R.ok(service.setStatus(houseId, cmd.start(), cmd.end(), cmd.dayStatus(),
                cmd.remark()));
    }

    /** 当日调价。 */
    @PostMapping("/{houseId}/price")
    public R<DayCellVO> setPrice(@PathVariable Long houseId, @RequestBody PriceCmd cmd) {
        return R.ok(service.setPrice(houseId, cmd.date(), cmd.price()));
    }

    public record ReleaseCmd(Long houseId,
                             @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate checkIn,
                             @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate checkOut,
                             Long bookingId) {
    }

    public record StatusCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
            String dayStatus, String remark) {
    }

    public record PriceCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date, BigDecimal price) {
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
