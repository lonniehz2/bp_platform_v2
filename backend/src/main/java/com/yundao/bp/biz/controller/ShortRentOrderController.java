package com.yundao.bp.biz.controller;

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

    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:short-rent-orders:create")
    @PostMapping
    public R<ShortRentOrderVO> create(@Valid @RequestBody ShortRentOrderCreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:short-rent-orders:view")
    @GetMapping("/{id}")
    public R<ShortRentOrderVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:short-rent-orders:view")
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
    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:by-house:view")
    @GetMapping("/by-house")
    public R<PageResult<ShortRentOrderVO>> byHouse(
            @RequestParam Long houseId,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date,
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize) {
        return R.ok(service.listByHouseAndDate(houseId, date, pageNum, pageSize));
    }

    /** 房晚试算。 */
    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:calc-nights:calc")
    @GetMapping("/calc-nights")
    public R<Integer> calcNights(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime checkIn,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
            LocalDateTime checkOut) {
        return R.ok(service.calcNights(checkIn, checkOut));
    }

    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:confirm:create")
    @PostMapping("/{id}/confirm")
    public R<ShortRentOrderVO> confirm(@PathVariable Long id) {
        return R.ok(service.confirm(id));
    }

    /** 办理入住。 */
    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:check-in:create")
    @PostMapping("/{id}/check-in")
    public R<ShortRentOrderVO> checkIn(@PathVariable Long id) {
        return R.ok(service.checkIn(id));
    }

    /** 办理退房（可追加超时/消费费用）。 */
    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:check-out:create")
    @PostMapping("/{id}/check-out")
    public R<ShortRentOrderVO> checkOut(@PathVariable Long id,
                                        @RequestBody(required = false) ExtraCmd cmd) {
        return R.ok(service.checkOut(id, cmd == null ? null : cmd.extraAmount()));
    }

    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:cancel:cancel")
    @PostMapping("/{id}/cancel")
    public R<ShortRentOrderVO> cancel(@PathVariable Long id,
                                     @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.cancel(id, cmd == null ? null : cmd.reason()));
    }

    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:no-show:create")
    @PostMapping("/{id}/no-show")
    public R<ShortRentOrderVO> noShow(@PathVariable Long id) {
        return R.ok(service.markNoShow(id));
    }

    @com.yundao.bp.iam.security.RequirePerm("short-rent-orders:pay:pay")
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
