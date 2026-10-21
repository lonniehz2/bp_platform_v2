package com.yundao.bp.asset.controller;

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
