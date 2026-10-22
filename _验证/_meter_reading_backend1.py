# -*- coding: utf-8 -*-
"""能耗抄表（物业/园区）：录入读数 → 自动算用量 → 一键出账。

表：bp_fin_meter_reading
接口：
  POST /fin/meter-readings        录入读数（自动取上次读数算用量与金额）
  GET  /fin/meter-readings        分页
  POST /fin/meter-readings/{id}/bill  按读数生成账单（复用 BillingService.createBill）
"""
import io
import os

import pymysql

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()
cur.execute("show tables like 'bp_fin_meter_reading'")
if not cur.fetchone():
    cur.execute('''
        create table bp_fin_meter_reading (
          id bigint not null primary key,
          tenant_id varchar(32) not null,
          org_id bigint null,
          house_id bigint not null,
          fee_item_id bigint not null,
          read_date date not null,
          reading decimal(14,2) not null comment '本次读数',
          prev_reading decimal(14,2) null comment '上次读数',
          usage_amount decimal(14,2) null comment '用量',
          unit_price decimal(14,4) null,
          amount decimal(14,2) null,
          bill_status varchar(16) not null default 'UNBILLED' comment 'UNBILLED/BILLED',
          bill_id bigint null,
          remark varchar(255) null,
          create_by varchar(64) null,
          create_time datetime not null,
          is_deleted tinyint not null default 0,
          key idx_meter_house (tenant_id, house_id, fee_item_id, read_date)
        ) comment '能耗抄表读数'
    ''')
    conn.commit()
    print('表 bp_fin_meter_reading 已创建')
else:
    print('表已存在')
conn.close()

io.open(os.path.join(J, 'entity', 'FinMeterReading.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/** 能耗抄表读数（水电燃气等 METER 类收费）。 */
@Data
@TableName("bp_fin_meter_reading")
public class FinMeterReading {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long orgId;
    private Long houseId;
    private Long feeItemId;
    private LocalDate readDate;
    private BigDecimal reading;
    private BigDecimal prevReading;
    private BigDecimal usageAmount;
    private BigDecimal unitPrice;
    private BigDecimal amount;
    private String billStatus;
    private Long billId;
    private String remark;
    private String createBy;
    private LocalDateTime createTime;
    private Integer isDeleted;
}
''')

io.open(os.path.join(J, 'mapper', 'FinMeterReadingMapper.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.FinMeterReading;
import org.apache.ibatis.annotations.Mapper;

/** 抄表读数 Mapper。 */
@Mapper
public interface FinMeterReadingMapper extends BaseMapper<FinMeterReading> {
}
''')

io.open(os.path.join(J, 'dto', 'MeterReadingCmd.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 录入抄表读数。
 *
 * @param reading 本次读数（必须 ≥ 上次读数）
 * @param billPeriod 生成账单时的账期（可空，默认读数的年月）
 */
public record MeterReadingCmd(
        @NotNull(message = "房源不能为空") Long houseId,
        @NotNull(message = "收费项目不能为空") Long feeItemId,
        @NotNull(message = "读数不能为空") BigDecimal reading,
        LocalDate readDate,
        String billPeriod,
        String remark) {
}
''')

io.open(os.path.join(J, 'service', 'MeterReadingService.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.MeterReadingCmd;
import com.yundao.bp.fin.entity.FinMeterReading;

/** 能耗抄表。 */
public interface MeterReadingService {

    FinMeterReading record(MeterReadingCmd cmd);

    PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId, Long feeItemId);

    /** 按读数生成账单。 */
    BillVO bill(Long readingId);
}
''')
print('实体/Mapper/DTO/Service 接口 已生成')
