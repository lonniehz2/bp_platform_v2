package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.FinDevicePrepayAccount;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface FinDevicePrepayAccountMapper extends BaseMapper<FinDevicePrepayAccount> {
    @Select("select * from bp_fin_device_prepay_account where tenant_id = #{tenantId} "
            + "and meter_point_id = #{meterPointId} for update")
    FinDevicePrepayAccount lockByPoint(String tenantId, Long meterPointId);
}
