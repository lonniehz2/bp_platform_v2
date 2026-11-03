package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.FinPrepayAccount;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface FinPrepayAccountMapper extends BaseMapper<FinPrepayAccount> {
    @Select("select * from bp_fin_prepay_account where tenant_id = #{tenantId} "
            + "and contract_id = #{contractId} for update")
    FinPrepayAccount lockByContract(String tenantId, Long contractId);
}
