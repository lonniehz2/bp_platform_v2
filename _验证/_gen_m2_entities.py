# -*- coding: utf-8 -*-
import io
import os

BASE = r'..\backend\src\main\java\com\yundao\bp\fin'
files = {}

def entity(name, table, comment, fields):
    body = '\n'.join('    private %s %s;' % (t, n) for t, n in fields)
    return '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/** %s */
@Data
@TableName("%s")
public class %s {
    @TableId(type = IdType.INPUT)
    private Long id;
%s
}
''' % (comment, table, name, body)

files['entity/MeterPoint.java'] = entity('MeterPoint', 'bp_fin_meter_point', '表计点位', [
    ('String', 'tenantId'), ('Long', 'spaceId'), ('Long', 'feeItemId'),
    ('String', 'meterScope'), ('String', 'allocationBasis'), ('String', 'meterName'),
    ('String', 'status'), ('LocalDateTime', 'createTime'), ('LocalDateTime', 'updateTime')])

files['entity/UtilityAllocation.java'] = entity('UtilityAllocation', 'bp_fin_utility_allocation', '能耗分摊主单', [
    ('String', 'tenantId'), ('Long', 'meterPointId'), ('String', 'period'),
    ('BigDecimal', 'startReading'), ('BigDecimal', 'endReading'), ('BigDecimal', 'totalUsage'),
    ('BigDecimal', 'totalAmount'), ('BigDecimal', 'operatorBearAmount'),
    ('String', 'tierDetail'), ('String', 'status'), ('LocalDateTime', 'createTime')])

files['entity/UtilityShare.java'] = entity('UtilityShare', 'bp_fin_utility_share', '能耗分摊明细', [
    ('String', 'tenantId'), ('Long', 'allocationId'), ('Long', 'contractId'),
    ('Long', 'personId'), ('Integer', 'occupyDays'), ('BigDecimal', 'personDays'),
    ('BigDecimal', 'shareRatio'), ('BigDecimal', 'shareAmount'),
    ('BigDecimal', 'roundingDelta'), ('Long', 'billId')])

files['entity/EnergyPolicy.java'] = entity('EnergyPolicy', 'bp_fin_energy_policy', '能耗策略', [
    ('String', 'tenantId'), ('Long', 'orgId'), ('String', 'vacancyBearer'),
    ('BigDecimal', 'warnRate'), ('BigDecimal', 'alarmRate'), ('String', 'status'),
    ('LocalDateTime', 'createTime'), ('LocalDateTime', 'updateTime')])

files['entity/EnergyMonthlyStat.java'] = entity('EnergyMonthlyStat', 'bp_fin_energy_monthly_stat', '总表分表月度统计', [
    ('String', 'tenantId'), ('String', 'period'), ('Long', 'spaceId'),
    ('BigDecimal', 'totalUsage'), ('BigDecimal', 'submeterUsage'),
    ('BigDecimal', 'diffUsage'), ('BigDecimal', 'diffRate'),
    ('String', 'alertLevel'), ('LocalDateTime', 'createTime')])

files['entity/LateFeePolicy.java'] = entity('LateFeePolicy', 'bp_fin_late_fee_policy', '滞纳金策略', [
    ('String', 'tenantId'), ('Long', 'orgId'), ('BigDecimal', 'dailyRate'),
    ('Integer', 'graceDays'), ('BigDecimal', 'capRate'), ('String', 'status'),
    ('LocalDateTime', 'createTime'), ('LocalDateTime', 'updateTime')])

files['entity/DepositTransfer.java'] = entity('DepositTransfer', 'bp_fin_deposit_transfer', '押金转移', [
    ('String', 'tenantId'), ('Long', 'exchangeId'), ('Long', 'oldContractId'),
    ('Long', 'newContractId'), ('Long', 'oldDepositId'), ('Long', 'newDepositId'),
    ('BigDecimal', 'transferAmount'), ('Long', 'operatorId'), ('LocalDateTime', 'createTime')])

files['mapper/MeterPointMapper.java'] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.MeterPoint;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MeterPointMapper extends BaseMapper<MeterPoint> {
}
'''
files['mapper/UtilityAllocationMapper.java'] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.UtilityAllocation;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UtilityAllocationMapper extends BaseMapper<UtilityAllocation> {
}
'''
files['mapper/UtilityShareMapper.java'] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.UtilityShare;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UtilityShareMapper extends BaseMapper<UtilityShare> {
}
'''
files['mapper/EnergyPolicyMapper.java'] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.EnergyPolicy;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface EnergyPolicyMapper extends BaseMapper<EnergyPolicy> {
}
'''
files['mapper/EnergyMonthlyStatMapper.java'] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.EnergyMonthlyStat;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface EnergyMonthlyStatMapper extends BaseMapper<EnergyMonthlyStat> {
}
'''
files['mapper/LateFeePolicyMapper.java'] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.LateFeePolicy;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface LateFeePolicyMapper extends BaseMapper<LateFeePolicy> {
}
'''
files['mapper/DepositTransferMapper.java'] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.DepositTransfer;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DepositTransferMapper extends BaseMapper<DepositTransfer> {
}
'''

for rel, code in files.items():
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, 'w', encoding='utf-8', newline='').write(code)
print('entities/mappers', len(files))
