# -*- coding: utf-8 -*-
"""抄表服务实现 + Controller。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

io.open(os.path.join(J, 'service', 'impl', 'MeterReadingServiceImpl.java'), 'w',
        encoding='utf-8', newline='').write('''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.dto.BillCreateCmd;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.MeterReadingCmd;
import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.entity.FinMeterReading;
import com.yundao.bp.fin.mapper.FinFeeItemMapper;
import com.yundao.bp.fin.mapper.FinMeterReadingMapper;
import com.yundao.bp.fin.service.BillingService;
import com.yundao.bp.fin.service.MeterReadingService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 能耗抄表：录入读数、算用量、一键出账。 */
@Service
public class MeterReadingServiceImpl implements MeterReadingService {

    private final FinMeterReadingMapper mapper;
    private final FinFeeItemMapper feeItemMapper;
    private final BillingService billingService;
    private final SnowflakeIdGenerator idGen;

    public MeterReadingServiceImpl(FinMeterReadingMapper mapper, FinFeeItemMapper feeItemMapper,
                                   BillingService billingService, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.feeItemMapper = feeItemMapper;
        this.billingService = billingService;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FinMeterReading record(MeterReadingCmd cmd) {
        FinFeeItem item = feeItemMapper.selectById(cmd.feeItemId());
        if (item == null) {
            throw BizException.notFound("收费项目");
        }
        if (!"METER".equals(item.getCalcMode())) {
            throw BizException.paramInvalid("该收费项目不是「按抄表」计费，请用批量出账");
        }
        LocalDate readDate = cmd.readDate() == null ? LocalDate.now() : cmd.readDate();

        // 上次读数：同房源同项目、读数日期早于本次的最近一条
        FinMeterReading prev = mapper.selectOne(new LambdaQueryWrapper<FinMeterReading>()
                .eq(FinMeterReading::getHouseId, cmd.houseId())
                .eq(FinMeterReading::getFeeItemId, cmd.feeItemId())
                .lt(FinMeterReading::getReadDate, readDate)
                .orderByDesc(FinMeterReading::getReadDate)
                .last("LIMIT 1"));
        BigDecimal prevReading = prev == null ? BigDecimal.ZERO : prev.getReading();
        if (cmd.reading().compareTo(prevReading) < 0) {
            throw BizException.paramInvalid("本次读数不能小于上次读数（上次 " + prevReading + "）");
        }
        BigDecimal usage = cmd.reading().subtract(prevReading);
        BigDecimal price = item.getUnitPrice() == null ? BigDecimal.ZERO : item.getUnitPrice();
        BigDecimal amount = usage.multiply(price).setScale(2, RoundingMode.HALF_UP);

        FinMeterReading e = new FinMeterReading();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setOrgId(null);
        e.setHouseId(cmd.houseId());
        e.setFeeItemId(cmd.feeItemId());
        e.setReadDate(readDate);
        e.setReading(cmd.reading());
        e.setPrevReading(prevReading);
        e.setUsageAmount(usage);
        e.setUnitPrice(price);
        e.setAmount(amount);
        e.setBillStatus("UNBILLED");
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        e.setCreateTime(LocalDateTime.now());
        mapper.insert(e);
        return e;
    }

    @Override
    public PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId,
                                            Long feeItemId) {
        LambdaQueryWrapper<FinMeterReading> qw = new LambdaQueryWrapper<FinMeterReading>()
                .eq(houseId != null, FinMeterReading::getHouseId, houseId)
                .eq(feeItemId != null, FinMeterReading::getFeeItemId, feeItemId)
                .orderByDesc(FinMeterReading::getReadDate);
        var page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BillVO bill(Long readingId) {
        FinMeterReading e = mapper.selectById(readingId);
        if (e == null) {
            throw BizException.notFound("抄表记录");
        }
        if ("BILLED".equals(e.getBillStatus())) {
            throw BizException.paramInvalid("该抄表记录已出账");
        }
        String period = e.getReadDate().toString().substring(0, 7).replace("-", "");
        BillCreateCmd cmd = new BillCreateCmd(
                e.getFeeItemId(), e.getOrgId(), null, e.getHouseId(), null, null,
                null, null, period, e.getReadDate(), e.getReadDate(),
                e.getAmount(), null, null, null, "METER", "抄表出账：" + e.getUsageAmount()
                + " × " + e.getUnitPrice());
        BillVO bill = billingService.createBill(cmd);
        e.setBillStatus("BILLED");
        e.setBillId(bill.id());
        mapper.updateById(e);
        return bill;
    }
}
''')

io.open(os.path.join(J, 'controller', 'MeterReadingController.java'), 'w', encoding='utf-8',
        newline='').write('''package com.yundao.bp.fin.controller;

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
''')
print('抄表 Service 实现与 Controller 已生成')
