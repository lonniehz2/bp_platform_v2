package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.MeterReadingCmd;
import com.yundao.bp.fin.entity.FinMeterReading;
import com.yundao.bp.fin.service.MeterReadingService;
import com.yundao.bp.iam.security.RequirePerm;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 能耗抄表（水电燃气）。 */
@RestController
@RequestMapping("/api/v1/fin/meter-readings")
public class MeterReadingController {

    private final MeterReadingService service;

    public MeterReadingController(MeterReadingService service) {
        this.service = service;
    }

    @PostMapping
    @RequirePerm("fin:bill:create")
    public R<FinMeterReading> record(@Valid @RequestBody MeterReadingCmd cmd) {
        return R.ok(service.record(cmd));
    }

    @GetMapping
    @RequirePerm("fin:bill:view")
    public R<PageResult<FinMeterReading>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long houseId,
            @RequestParam(required = false) Long feeItemId) {
        return R.ok(service.page(pageNum, pageSize, houseId, feeItemId));
    }

    /** 按读数生成账单。 */
    @PostMapping("/{id}/bill")
    @RequirePerm("fin:bill:create")
    public R<BillVO> bill(@PathVariable Long id) {
        return R.ok(service.bill(id));
    }
}
