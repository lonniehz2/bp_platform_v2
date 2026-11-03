package com.yundao.bp.fin.service;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

/** 财务多口径汇总：费用所属期、账单生成、现金收款、预收负债。 */
@Service
public class FinanceReportService {

    private final JdbcTemplate jdbc;

    public FinanceReportService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Map<String, Object> overview(String period) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("period", period);
        out.put("billReceivable", money(jdbc.queryForObject(
                "select coalesce(sum(bill_amount),0) from bp_fin_bill "
                        + "where bill_period = ? and is_deleted = 0", BigDecimal.class, period)));
        out.put("billGenerated", money(jdbc.queryForObject(
                "select coalesce(sum(bill_amount),0) from bp_fin_bill where is_deleted = 0 "
                        + "and date_format(coalesce(bill_date, date(create_time)), '%Y-%m') = ?",
                BigDecimal.class, period)));
        out.put("subsidy", money(jdbc.queryForObject(
                "select coalesce(sum(subsidy_amount),0) from bp_fin_subsidy_record "
                        + "where subsidy_period = ?", BigDecimal.class, period)));
        BigDecimal directCash = jdbc.queryForObject(
                "select coalesce(sum(pay_amount),0) from bp_fin_payment "
                        + "where pay_status = 'SUCCESS' and pay_channel not in ('PREPAY','DEVICE_PREPAY') "
                        + "and date_format(pay_time, '%Y-%m') = ?",
                BigDecimal.class, period);
        BigDecimal prepayIn = jdbc.queryForObject(
                "select coalesce(sum(amount),0) from bp_fin_prepay_flow "
                        + "where flow_type = 'IN' and date_format(create_time, '%Y-%m') = ?",
                BigDecimal.class, period);
        BigDecimal deviceIn = jdbc.queryForObject(
                "select coalesce(sum(amount),0) from bp_fin_device_prepay_flow "
                        + "where flow_type = 'IN' and date_format(create_time, '%Y-%m') = ?",
                BigDecimal.class, period);
        out.put("cashIn", money(directCash.add(prepayIn).add(deviceIn)));
        out.put("prepayRefund", money(jdbc.queryForObject(
                "select coalesce(sum(amount),0) from bp_fin_prepay_flow "
                        + "where flow_type = 'REFUND' and date_format(create_time, '%Y-%m') = ?",
                BigDecimal.class, period)));
        out.put("deviceRefund", money(jdbc.queryForObject(
                "select coalesce(sum(amount),0) from bp_fin_device_prepay_flow "
                        + "where flow_type = 'REFUND' and date_format(create_time, '%Y-%m') = ?",
                BigDecimal.class, period)));
        out.put("prepayBalance", money(jdbc.queryForObject(
                "select coalesce(sum(balance_amount),0) from bp_fin_prepay_account",
                BigDecimal.class)));
        out.put("devicePrepayBalance", money(jdbc.queryForObject(
                "select coalesce(sum(balance_amount),0) from bp_fin_device_prepay_account",
                BigDecimal.class)));
        out.put("outstanding", money(jdbc.queryForObject(
                "select coalesce(sum(payable_amount),0) from bp_fin_bill "
                        + "where is_deleted = 0 and bill_status in ('UNPAID','PARTIAL','OVERDUE')",
                BigDecimal.class)));
        out.put("overdueAmount", money(jdbc.queryForObject(
                "select coalesce(sum(payable_amount),0) from bp_fin_bill "
                        + "where is_deleted = 0 and bill_status in ('UNPAID','PARTIAL','OVERDUE') "
                        + "and due_date < curdate()", BigDecimal.class)));
        out.put("billCount", jdbc.queryForObject(
                "select count(*) from bp_fin_bill where bill_period = ? and is_deleted = 0",
                Long.class, period));
        return out;
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, java.math.RoundingMode.HALF_UP);
    }
}
