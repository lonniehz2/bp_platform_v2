package com.yundao.bp.fin.service.impl;

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

    /** 房源（取组织） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper;

    /** 合同（取在租承租人） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizContractMapper contractMapper;
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
        // 费用区间：上次抄表日（无则本次往前推一个月）→ 本次抄表日；截止日必须晚于起始日
        java.time.LocalDate start = e.getReadDate().minusMonths(1);
        com.yundao.bp.asset.entity.AssetHouse house = houseMapper == null
                ? null : houseMapper.selectById(e.getHouseId());
        java.time.LocalDate prevRead = null;
        FinMeterReading prev = mapper.selectOne(new LambdaQueryWrapper<FinMeterReading>()
                .eq(FinMeterReading::getHouseId, e.getHouseId())
                .eq(FinMeterReading::getFeeItemId, e.getFeeItemId())
                .lt(FinMeterReading::getReadDate, e.getReadDate())
                .orderByDesc(FinMeterReading::getReadDate)
                .last("LIMIT 1"));
        if (prev != null) {
            start = prev.getReadDate();
        }
        if (!e.getReadDate().isAfter(start)) {
            start = e.getReadDate().minusDays(1);
        }
        Long orgId = e.getOrgId() != null ? e.getOrgId()
                : (house == null ? null : house.getOrgId());
        // 在租合同（用于挂缴费人）
        com.yundao.bp.biz.entity.BizContract contract = contractMapper == null ? null
                : contractMapper.selectOne(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                <com.yundao.bp.biz.entity.BizContract>()
                                .eq(com.yundao.bp.biz.entity.BizContract::getHouseId, e.getHouseId())
                                .eq(com.yundao.bp.biz.entity.BizContract::getContractStatus,
                                        "EFFECTIVE")
                                .last("LIMIT 1"));
        BillCreateCmd cmd = new BillCreateCmd(
                e.getFeeItemId(), orgId,
                contract == null ? null : contract.getId(), e.getHouseId(),
                house == null ? null : house.getSpaceId(),
                contract == null ? null : contract.getLesseePersonId(),
                contract == null ? null : contract.getLesseeName(),
                contract == null ? null : contract.getLesseePhone(),
                period, start, e.getReadDate(),
                e.getAmount(), null, null, null, "METER", "抄表出账：" + e.getUsageAmount()
                + " × " + e.getUnitPrice());
        if (orgId != null && e.getOrgId() == null) {
            e.setOrgId(orgId);
        }
        BillVO bill = billingService.createBill(cmd);
        e.setBillStatus("BILLED");
        e.setBillId(bill.id());
        mapper.updateById(e);
        return bill;
    }
}
