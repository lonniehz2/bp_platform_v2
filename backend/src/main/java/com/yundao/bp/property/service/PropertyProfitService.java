package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.sql.Date;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 物业支出与项目经营报表。 */
@Service
public class PropertyProfitService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;

    public PropertyProfitService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> expenses(Long projectId, String month) {
        requireProject(projectId);
        LocalDate first = firstDay(month);
        return jdbc.queryForList(
                "select e.id, e.expense_month expenseMonth, e.category_code categoryCode, "
                        + "e.subcategory_code subcategoryCode, e.amount, e.supplier, e.invoice_no invoiceNo, "
                        + "e.pay_method payMethod, e.remark, c.category_name categoryName "
                        + "from prop_expense e left join prop_category c on c.category_code=e.category_code "
                        + "and c.category_type='EXPENSE' and c.tenant_id=e.tenant_id "
                        + "where e.tenant_id=? and e.project_id=? and e.is_deleted=0 "
                        + "and e.expense_month between ? and ? order by e.id desc",
                TenantContext.tenantId(), projectId, Date.valueOf(first),
                Date.valueOf(first.plusMonths(1).minusDays(1)));
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> createExpense(Long projectId, ExpenseCmd cmd) {
        requireProject(projectId);
        if (cmd.amount() == null || cmd.amount().compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("支出金额必须大于 0");
        }
        if (cmd.categoryCode() == null || cmd.categoryCode().isBlank()) {
            throw BizException.paramInvalid("请选择支出分类");
        }
        LocalDate month = firstDay(cmd.expenseMonth());
        long id = idGen.nextId();
        jdbc.update("insert into prop_expense(id,tenant_id,project_id,expense_month,category_code,"
                        + "subcategory_code,amount,supplier,invoice_no,pay_method,remark,status,is_deleted,"
                        + "create_by,create_time,update_by,update_time) values(?,?,?,?,?,?,?,?,?,?,?, 'CONFIRMED',0,?,now(),?,now())",
                id, TenantContext.tenantId(), projectId, Date.valueOf(month),
                cmd.categoryCode(), cmd.subcategoryCode(), cmd.amount(), cmd.supplier(),
                cmd.invoiceNo(), cmd.payMethod(), cmd.remark(),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        return Map.of("id", id);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> deleteExpense(Long id) {
        int n = jdbc.update("update prop_expense set is_deleted=1, update_time=now() "
                + "where id=? and tenant_id=?", id, TenantContext.tenantId());
        if (n == 0) throw BizException.notFound("支出");
        return Map.of("deleted", n);
    }

    public Map<String, Object> overview(Long projectId, String month) {
        requireProject(projectId);
        LocalDate first = firstDay(month);
        LocalDate last = first.plusMonths(1).minusDays(1);
        BigDecimal income = jdbc.queryForObject(
                "select coalesce(sum(pay_amount),0) from prop_payment where tenant_id=? and project_id=? "
                        + "and pay_status='SUCCESS' and pay_time >= ? and pay_time < ?",
                BigDecimal.class, TenantContext.tenantId(), projectId,
                Date.valueOf(first), Date.valueOf(first.plusMonths(1)));
        BigDecimal receivable = jdbc.queryForObject(
                "select coalesce(sum(payable_amount),0) from prop_bill where tenant_id=? and project_id=? "
                        + "and is_deleted=0 and period_start <= ? and period_end >= ?",
                BigDecimal.class, TenantContext.tenantId(), projectId,
                Date.valueOf(last), Date.valueOf(first));
        BigDecimal expense = jdbc.queryForObject(
                "select coalesce(sum(amount),0) from prop_expense where tenant_id=? and project_id=? "
                        + "and is_deleted=0 and expense_month between ? and ?",
                BigDecimal.class, TenantContext.tenantId(), projectId,
                Date.valueOf(first), Date.valueOf(last));
        List<Map<String, Object>> incomeRows = jdbc.queryForList(
                "select b.income_category incomeCategory, coalesce(sum(a.allocate_amount),0) amount "
                        + "from prop_payment_allocation a join prop_payment p on p.id=a.payment_id "
                        + "join prop_bill b on b.id=a.bill_id where p.tenant_id=? and p.project_id=? "
                        + "and p.pay_status='SUCCESS' and p.pay_time >= ? and p.pay_time < ? "
                        + "group by b.income_category order by amount desc",
                TenantContext.tenantId(), projectId, Date.valueOf(first), Date.valueOf(first.plusMonths(1)));
        List<Map<String, Object>> expenseRows = jdbc.queryForList(
                "select e.category_code categoryCode, c.category_name categoryName, "
                        + "coalesce(sum(e.amount),0) amount from prop_expense e "
                        + "left join prop_category c on c.category_code=e.category_code "
                        + "and c.category_type='EXPENSE' and c.tenant_id=e.tenant_id "
                        + "where e.tenant_id=? and e.project_id=? and e.is_deleted=0 "
                        + "and e.expense_month between ? and ? group by e.category_code, c.category_name "
                        + "order by amount desc",
                TenantContext.tenantId(), projectId, Date.valueOf(first), Date.valueOf(last));
        BigDecimal rate = receivable.compareTo(BigDecimal.ZERO) == 0
                ? BigDecimal.ZERO
                : income.multiply(BigDecimal.valueOf(100)).divide(receivable, 1, java.math.RoundingMode.HALF_UP);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("month", YearMonth.from(first).toString());
        out.put("income", income);
        out.put("receivable", receivable);
        out.put("expense", expense);
        out.put("profit", income.subtract(expense));
        out.put("collectionRate", rate);
        out.put("incomeRows", incomeRows);
        out.put("expenseRows", expenseRows);
        return out;
    }

    public List<Map<String, Object>> expenseCategories() {
        return jdbc.queryForList(
                "select id, category_code categoryCode, category_name categoryName, parent_id parentId, "
                        + "category_level categoryLevel from prop_category where tenant_id=? "
                        + "and category_type='EXPENSE' and is_deleted=0 order by sort_no, id",
                TenantContext.tenantId());
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }

    private static LocalDate firstDay(String month) {
        if (month == null || month.isBlank()) return LocalDate.now().withDayOfMonth(1);
        try {
            return YearMonth.parse(month).atDay(1);
        } catch (Exception e) {
            throw BizException.paramInvalid("月份格式应为 yyyy-MM");
        }
    }

    public record ExpenseCmd(String expenseMonth, String categoryCode, String subcategoryCode,
                             BigDecimal amount, String supplier, String invoiceNo,
                             String payMethod, String remark) {
    }
}
