# -*- coding: utf-8 -*-
"""性能优化：
1) 指标聚合改 SQL 聚合（原来加载全表到 Java 求和，数据量大时会 OOM/超时）
2) 大屏复用一次 currentAll（原来 8 组件各查一遍）
3) 补 bp_fin_bill(tenant_id, bill_status) 索引
"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ---------- 1) FinBillMapper 增加 SQL 聚合 ----------
p1 = os.path.join(BASE, r'fin\mapper\FinBillMapper.java')
s1 = io.open(p1, encoding='utf-8').read()
if 'sumUnpaidPayable' not in s1:
    s1 = '''package com.yundao.bp.fin.mapper;

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
}
'''
    io.open(p1, 'w', encoding='utf-8').write(s1)
    print('  ✓ FinBillMapper 增加 SQL 聚合')

# ---------- 2) FinPaymentMapper 增加 SQL 聚合 ----------
p2 = os.path.join(BASE, r'fin\mapper\FinPaymentMapper.java')
s2 = io.open(p2, encoding='utf-8').read()
if 'sumSuccessPayAmount' not in s2:
    s2 = '''package com.yundao.bp.fin.mapper;

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
'''
    io.open(p2, 'w', encoding='utf-8').write(s2)
    print('  ✓ FinPaymentMapper 增加 SQL 聚合')

# ---------- 3) MetricServiceImpl 改用聚合 ----------
p3 = os.path.join(BASE, r'rpt\service\impl\MetricServiceImpl.java')
s3 = io.open(p3, encoding='utf-8').read()
if 'sumUnpaidPayable' not in s3:
    s3 = s3.replace('''            case "BILL_UNPAID_COUNT" -> count(billMapper.selectCount(
                    new LambdaQueryWrapper<FinBill>()
                            .eq(orgId != null, FinBill::getOrgId, orgId)
                            .in(FinBill::getBillStatus,
                                    List.of("UNPAID", "PARTIAL", "OVERDUE"))));
            case "BILL_UNPAID_AMOUNT" -> sum(billMapper.selectList(
                    new LambdaQueryWrapper<FinBill>()
                            .eq(orgId != null, FinBill::getOrgId, orgId)
                            .in(FinBill::getBillStatus,
                                    List.of("UNPAID", "PARTIAL", "OVERDUE"))));''',
                  '''            case "BILL_UNPAID_COUNT" -> count(billMapper.countUnpaid(
                    TenantContext.tenantId(), orgId));
            case "BILL_UNPAID_AMOUNT" -> money(billMapper.sumUnpaidPayable(
                    TenantContext.tenantId(), orgId));''')
    s3 = s3.replace('''            case "PAYMENT_TOTAL_AMOUNT" -> sumPayments(orgId);''',
                  '''            case "PAYMENT_TOTAL_AMOUNT" -> money(paymentMapper.sumSuccessPayAmount(
                    TenantContext.tenantId(), orgId));''')
    # 移除不再使用的方法 sum(List) 与 sumPayments
    s3 = s3.replace('''    private static double sum(List<FinBill> bills) {
        BigDecimal s = BigDecimal.ZERO;
        for (FinBill b : bills) {
            s = s.add(b.getPayableAmount() == null ? BigDecimal.ZERO : b.getPayableAmount());
        }
        return s.setScale(2, RoundingMode.HALF_UP).doubleValue();
    }

    private double sumPayments(Long orgId) {
        List<FinPayment> list = paymentMapper.selectList(
                new LambdaQueryWrapper<FinPayment>()
                        .eq(orgId != null, FinPayment::getOrgId, orgId)
                        .eq(FinPayment::getPayStatus, "SUCCESS"));
        BigDecimal s = BigDecimal.ZERO;
        for (FinPayment p : list) {
            s = s.add(p.getPayAmount() == null ? BigDecimal.ZERO : p.getPayAmount());
        }
        return s.setScale(2, RoundingMode.HALF_UP).doubleValue();
    }''',
                  '''    private static double money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v)
                .setScale(2, RoundingMode.HALF_UP).doubleValue();
    }''')
    io.open(p3, 'w', encoding='utf-8').write(s3)
    print('  ✓ MetricServiceImpl 改用 SQL 聚合（去掉全表加载）')

# ---------- 4) 大屏复用 currentAll ----------
p4 = os.path.join(BASE, r'rpt\service\impl\ScreenServiceImpl.java')
s4 = io.open(p4, encoding='utf-8').read()
if 'currentAll(orgId)' not in s4:
    s4 = s4.replace('''        List<Map<String, Object>> out = new ArrayList<>();''',
                    '''        // 一次性取全部指标，避免每个组件重复查询（原来 8 组件 = 8 轮聚合）
        Map<String, Object> all = metricService.currentAll(orgId);
        List<Map<String, Object>> out = new ArrayList<>();''')
    s4 = s4.replace('''                item.put("value", metricService.current(code, orgId));''',
                    '''                Object v = all.get(code);
                item.put("value", v == null ? 0.0 : v);''')
    io.open(p4, 'w', encoding='utf-8').write(s4)
    print('  ✓ ScreenServiceImpl 复用 currentAll（8 轮聚合 → 1 轮）')

# ---------- 5) 补索引 ----------
import pymysql  # noqa: E402
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()
cur.execute("SHOW INDEX FROM bp_fin_bill")
existing = {r[2] for r in cur.fetchall()}
if 'idx_tenant_billstatus' not in existing:
    cur.execute("ALTER TABLE bp_fin_bill ADD INDEX idx_tenant_billstatus "
                "(tenant_id, bill_status, payable_amount)")
    print('  ✓ 新增索引 idx_tenant_billstatus(tenant_id, bill_status, payable_amount)')
else:
    print('  - 索引已存在')
cur.execute("SHOW INDEX FROM bp_fin_payment")
existing2 = {r[2] for r in cur.fetchall()}
if 'idx_tenant_paystatus' not in existing2:
    cur.execute("ALTER TABLE bp_fin_payment ADD INDEX idx_tenant_paystatus "
                "(tenant_id, pay_status, pay_amount)")
    print('  ✓ 新增索引 idx_tenant_paystatus(tenant_id, pay_status, pay_amount)')
c.commit()
c.close()
