package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.FinBill;
import java.math.BigDecimal;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface FinBillMapper extends BaseMapper<FinBill> {

    /**
     * 未缴账单应付合计（SQL 聚合）。
     *
     * <p>比「查出全部行再在 Java 求和」快一个量级：不传输、不实例化对象、
     * 数据量大时不会 OOM。原生 SQL 绕过租户拦截器，故必须显式传 tenantId。
     */
    @Select("<script>SELECT COALESCE(SUM(payable_amount),0) FROM bp_fin_bill "
            + "WHERE tenant_id = #{tenantId} "
            + "AND bill_status IN ('UNPAID','PARTIAL','OVERDUE') "
            + "<if test='orgId != null'>AND org_id = #{orgId}</if></script>")
    BigDecimal sumUnpaidPayable(@Param("tenantId") String tenantId,
                                @Param("orgId") Long orgId);

    /** 未缴/部分缴/逾期账单数（SQL 聚合）。 */
    @Select("<script>SELECT COUNT(*) FROM bp_fin_bill WHERE tenant_id = #{tenantId} "
            + "AND bill_status IN ('UNPAID','PARTIAL','OVERDUE') "
            + "<if test='orgId != null'>AND org_id = #{orgId}</if></script>")
    Long countUnpaid(@Param("tenantId") String tenantId, @Param("orgId") Long orgId);

    /**
     * 行级排他锁：返回主键即代表当前事务已持有该行锁。
     *
     * <p>用于跨实例并发保护（JVM 锁只在单实例有效）。必须在事务内调用。
     */
    @org.apache.ibatis.annotations.Select("select id from bp_fin_bill where id = #{id} for update")
    Long lockForUpdate(@org.apache.ibatis.annotations.Param("id") Long id);
}
