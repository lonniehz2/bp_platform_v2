package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.FinPayment;
import java.math.BigDecimal;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface FinPaymentMapper extends BaseMapper<FinPayment> {

    /** 成功收款合计（SQL 聚合，避免全表加载）。 */
    @Select("<script>SELECT COALESCE(SUM(pay_amount),0) FROM bp_fin_payment "
            + "WHERE tenant_id = #{tenantId} AND pay_status = 'SUCCESS' "
            + "<if test='orgId != null'>AND org_id = #{orgId}</if></script>")
    BigDecimal sumSuccessPayAmount(@Param("tenantId") String tenantId,
                                   @Param("orgId") Long orgId);
}
