package com.yundao.platform.service;

import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class DashboardService {

    private final JdbcTemplate jdbc;

    public DashboardService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Map<String, Object> summary(long projectId, LocalDate from, LocalDate to) {
        if (from == null || to == null || to.isBefore(from)) {
            throw new IllegalArgumentException("账期范围不合法");
        }
        String tenant = TenantContext.require();
        Map<String, Object> row = jdbc.queryForMap(
                "select "
                        + "coalesce(sum(case when (source_type is null or source_type <> 'OPENING') "
                        + "and period_start between ? and ? then payable_amount else 0 end),0) currentReceivable, "
                        + "coalesce(sum(case when (source_type is null or source_type <> 'OPENING') "
                        + "and period_start between ? and ? then paid_amount else 0 end),0) currentPaid, "
                        + "coalesce(sum(case when source_type = 'OPENING' then payable_amount - paid_amount else 0 end),0) openingOutstanding, "
                        + "coalesce(sum(case when source_type = 'OPENING' then paid_amount else 0 end),0) openingRecovery, "
                        + "coalesce(sum(case when source_type = 'OPENING' then payable_amount else 0 end),0) openingBase, "
                        + "count(*) billCount "
                        + "from bp_bill where tenant_id=? and project_id=? and is_deleted=0",
                from, to, from, to, tenant, projectId);
        BigDecimal receivable = value(row.get("currentReceivable"));
        BigDecimal paid = value(row.get("currentPaid"));
        BigDecimal opening = value(row.get("openingOutstanding"));
        BigDecimal openingRecovery = value(row.get("openingRecovery"));
        BigDecimal openingBase = value(row.get("openingBase"));
        BigDecimal currentOutstanding = receivable.subtract(paid).max(BigDecimal.ZERO);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("currentReceivable", receivable);
        out.put("currentPaid", paid);
        out.put("currentOutstanding", currentOutstanding);
        out.put("currentRate", percent(paid, receivable));
        out.put("openingOutstanding", opening);
        out.put("openingRecovery", openingRecovery);
        out.put("openingRate", percent(openingRecovery, openingBase));
        out.put("totalOutstanding", opening.add(currentOutstanding));
        out.put("billCount", row.get("billCount"));
        return out;
    }

    private static BigDecimal value(Object v) {
        return v == null ? BigDecimal.ZERO : (BigDecimal) v;
    }

    private static BigDecimal percent(BigDecimal a, BigDecimal b) {
        if (b == null || b.signum() == 0) return BigDecimal.ZERO;
        return a.multiply(BigDecimal.valueOf(100)).divide(b, 1, RoundingMode.HALF_UP);
    }
}
