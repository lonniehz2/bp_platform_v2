package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.sql.Date;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 物业收费闭环：收费项目、物业费账单、收款、电子收据。 */
@Service
public class PropertyBillingService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;

    public PropertyBillingService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> feeItems(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select id, fee_item_code feeItemCode, fee_item_name feeItemName, "
                        + "income_category incomeCategory, income_subcategory incomeSubcategory, "
                        + "charge_basis chargeBasis, billing_cycle billingCycle, unit, "
                        + "default_price defaultPrice, status "
                        + "from prop_fee_item where tenant_id=? and project_id=? and is_deleted=0 "
                        + "order by id", TenantContext.tenantId(), projectId);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> createFeeItem(Long projectId, FeeItemCmd cmd) {
        requireProject(projectId);
        if (cmd.feeItemCode() == null || cmd.feeItemCode().isBlank()
                || cmd.feeItemName() == null || cmd.feeItemName().isBlank()) {
            throw BizException.paramInvalid("收费项目编码和名称不能为空");
        }
        Long dup = jdbc.queryForObject("select count(*) from prop_fee_item "
                        + "where tenant_id=? and project_id=? and fee_item_code=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId, cmd.feeItemCode().trim());
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("收费项目编码已存在");
        }
        long id = idGen.nextId();
        jdbc.update("insert into prop_fee_item(id,tenant_id,project_id,fee_item_code,fee_item_name,"
                        + "income_category,income_subcategory,charge_basis,billing_cycle,unit,"
                        + "default_price,status,is_deleted,create_by,create_time,update_by,update_time) "
                        + "values(?,?,?,?,?,?,?,?,?,?,?, 'ENABLED',0,?,now(),?,now())",
                id, TenantContext.tenantId(), projectId, cmd.feeItemCode().trim(),
                cmd.feeItemName().trim(), cmd.incomeCategory(), cmd.incomeSubcategory(),
                cmd.chargeBasis(), cmd.billingCycle(), cmd.unit(),
                cmd.defaultPrice() == null ? BigDecimal.ZERO : cmd.defaultPrice(),
                String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
        return jdbc.queryForMap("select id, fee_item_code feeItemCode, fee_item_name feeItemName, "
                + "charge_basis chargeBasis, default_price defaultPrice from prop_fee_item where id=?", id);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> generateBills(GenerateCmd cmd) {
        requireProject(cmd.projectId());
        if (cmd.periodStart() == null || cmd.periodEnd() == null
                || cmd.periodEnd().isBefore(cmd.periodStart())) {
            throw BizException.paramInvalid("计费期间不合法");
        }
        Map<String, Object> fee = jdbc.queryForMap(
                "select * from prop_fee_item where id=? and tenant_id=? and project_id=? "
                        + "and is_deleted=0", cmd.feeItemId(), TenantContext.tenantId(), cmd.projectId());
        String basis = String.valueOf(fee.get("charge_basis"));
        if (!"AREA".equals(basis)) {
            throw BizException.paramInvalid("当前仅支持按建筑面积生成物业费账单");
        }
        BigDecimal price = (BigDecimal) fee.get("default_price");
        int months = months(cmd.periodStart(), cmd.periodEnd());
        List<Map<String, Object>> houses = jdbc.queryForList(
                "select id, space_id spaceId, house_name houseName, area, owner_person_id ownerPersonId, "
                        + "house_code houseCode from bp_asset_house "
                        + "where tenant_id=? and org_id=? and is_deleted=0 and area is not null and area>0 "
                        + "order by house_code", TenantContext.tenantId(), cmd.projectId());
        int created = 0, skipped = 0;
        for (Map<String, Object> h : houses) {
            Long houseId = ((Number) h.get("id")).longValue();
            Long exists = jdbc.queryForObject(
                    "select count(*) from prop_bill where tenant_id=? and project_id=? and fee_item_id=? "
                            + "and house_id=? and period_start=? and period_end=? and is_deleted=0",
                    Long.class, TenantContext.tenantId(), cmd.projectId(), cmd.feeItemId(),
                    houseId, Date.valueOf(cmd.periodStart()), Date.valueOf(cmd.periodEnd()));
            if (exists != null && exists > 0) {
                skipped++;
                continue;
            }
            BigDecimal area = (BigDecimal) h.get("area");
            BigDecimal amount = area.multiply(price).multiply(BigDecimal.valueOf(months))
                    .setScale(2, RoundingMode.HALF_UP);
            long id = idGen.nextId();
            String billNo = "PB" + id;
            Long payer = h.get("ownerPersonId") == null ? null : ((Number) h.get("ownerPersonId")).longValue();
            String payerName = str(h.get("houseName"));
            jdbc.update("insert into prop_bill(id,tenant_id,project_id,bill_no,income_category,"
                            + "income_subcategory,fee_item_id,payer_type,payer_person_id,payer_name,house_id,"
                            + "period_start,period_end,billing_cycle,cycle_count,quantity,unit_price,"
                            + "bill_amount,payable_amount,bill_status,due_date,source_type,source_id,"
                            + "service_start_date,service_end_date,is_deleted,create_by,create_time,update_by,update_time) "
                            + "values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'PENDING',?,?,?,?,?,0,?,now(),?,now())",
                    id, TenantContext.tenantId(), cmd.projectId(), billNo,
                    fee.get("income_category"), fee.get("income_subcategory"), cmd.feeItemId(),
                    payer == null ? "HOUSE" : "OWNER", payer, payerName, houseId,
                    Date.valueOf(cmd.periodStart()), Date.valueOf(cmd.periodEnd()),
                    "MONTH", months, area, price, amount, amount,
                    Date.valueOf(cmd.periodEnd()), "HOUSE", houseId,
                    Date.valueOf(cmd.periodStart()), Date.valueOf(cmd.periodEnd()),
                    String.valueOf(TenantContext.userId()), String.valueOf(TenantContext.userId()));
            created++;
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("total", houses.size());
        out.put("created", created);
        out.put("skipped", skipped);
        out.put("months", months);
        return out;
    }

    public Map<String, Object> pageBills(Long projectId, int pageNum, int pageSize,
                                         String status, String keyword) {
        requireProject(projectId);
        StringBuilder where = new StringBuilder(" from prop_bill b left join prop_fee_item f on f.id=b.fee_item_id "
                + "where b.tenant_id=? and b.project_id=? and b.is_deleted=0");
        List<Object> args = new ArrayList<>(List.of(TenantContext.tenantId(), projectId));
        if (status != null && !status.isBlank()) {
            where.append(" and b.bill_status=?");
            args.add(status);
        }
        if (keyword != null && !keyword.isBlank()) {
            where.append(" and (b.bill_no like ? or b.payer_name like ?)");
            args.add("%" + keyword.trim() + "%");
            args.add("%" + keyword.trim() + "%");
        }
        Long total = jdbc.queryForObject("select count(*)" + where, Long.class, args.toArray());
        args.add(pageSize);
        args.add((pageNum - 1) * pageSize);
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select b.id, b.bill_no billNo, b.payer_name payerName, b.house_id houseId, "
                        + "b.period_start periodStart, b.period_end periodEnd, b.bill_amount billAmount, "
                        + "b.payable_amount payableAmount, b.paid_amount paidAmount, b.bill_status billStatus, "
                        + "b.due_date dueDate, f.fee_item_name feeItemName "
                        + where + " order by b.id desc limit ? offset ?", args.toArray());
        // house name lookup for stable display
        for (Map<String, Object> r : rows) {
            if (r.get("houseId") != null) {
                try {
                    r.put("houseName", jdbc.queryForObject(
                            "select house_name from bp_asset_house where id=?", String.class, r.get("houseId")));
                } catch (Exception ignored) {
                    // 房源已删除时保留原值
                }
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("total", total);
        out.put("pageNum", pageNum);
        out.put("pageSize", pageSize);
        out.put("rows", rows);
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> pay(PayCmd cmd) {
        requireProject(cmd.projectId());
        if (cmd.billIds() == null || cmd.billIds().isEmpty()) {
            throw BizException.paramInvalid("请选择账单");
        }
        String channel = cmd.payChannel() == null ? "CASH" : cmd.payChannel().trim().toUpperCase();
        if (!List.of("WECHAT", "ALIPAY", "CASH", "BANK_TRANSFER", "POS").contains(channel)) {
            throw BizException.paramInvalid("收款方式不合法");
        }
        List<Map<String, Object>> bills = jdbc.queryForList(
                "select id, bill_no billNo, payable_amount payableAmount, paid_amount paidAmount, "
                        + "payer_person_id payerPersonId, payer_name payerName, bill_status billStatus "
                        + "from prop_bill where tenant_id=? and project_id=? and is_deleted=0 and id in ("
                        + placeholders(cmd.billIds().size()) + ")",
                concat(new Object[]{TenantContext.tenantId(), cmd.projectId()}, cmd.billIds()));
        if (bills.size() != cmd.billIds().size()) {
            throw BizException.notFound("账单");
        }
        BigDecimal total = BigDecimal.ZERO;
        for (Map<String, Object> b : bills) {
            if ("PAID".equals(b.get("billStatus")) || "CANCELLED".equals(b.get("billStatus"))) {
                throw BizException.stateConflict("账单已结清或已取消: " + b.get("billNo"));
            }
            BigDecimal payable = (BigDecimal) b.get("payableAmount");
            BigDecimal paid = (BigDecimal) b.get("paidAmount");
            total = total.add(payable.subtract(paid == null ? BigDecimal.ZERO : paid));
        }
        if (cmd.payAmount() == null || cmd.payAmount().compareTo(total) != 0) {
            throw BizException.paramInvalid("收款金额必须等于待收金额 " + total);
        }
        long paymentId = idGen.nextId();
        String payerName = str(bills.get(0).get("payerName"));
        Long payerId = bills.get(0).get("payerPersonId") == null ? null
                : ((Number) bills.get(0).get("payerPersonId")).longValue();
        jdbc.update("insert into prop_payment(id,tenant_id,project_id,payment_no,payer_person_id,payer_name,"
                        + "pay_amount,pay_channel,pay_status,pay_time,operator_id,remark,create_time,update_time) "
                        + "values(?,?,?,?,?,?,?,?, 'SUCCESS',now(),?,?,now(),now())",
                paymentId, TenantContext.tenantId(), cmd.projectId(), "PY" + paymentId,
                payerId, payerName, total, channel, TenantContext.userId(), cmd.remark());
        for (Map<String, Object> b : bills) {
            Long billId = ((Number) b.get("id")).longValue();
            BigDecimal payable = (BigDecimal) b.get("payableAmount");
            BigDecimal paid = (BigDecimal) b.get("paidAmount");
            BigDecimal due = payable.subtract(paid == null ? BigDecimal.ZERO : paid);
            jdbc.update("update prop_bill set paid_amount=payable_amount, bill_status='PAID', "
                    + "update_time=now() where id=?", billId);
            jdbc.update("insert into prop_payment_allocation(id,tenant_id,payment_id,bill_id,"
                            + "allocate_amount,create_time) values(?,?,?,?,?,now())",
                    idGen.nextId(), TenantContext.tenantId(), paymentId, billId, due);
        }
        long receiptId = idGen.nextId();
        String receiptNo = "PJ" + receiptId;
        jdbc.update("insert into prop_receipt(id,tenant_id,project_id,receipt_no,payment_id,payer_name,"
                        + "amount,receipt_status,verify_code,issued_at,create_time,update_time) "
                        + "values(?,?,?,?,?,?,?, 'ISSUED',?,now(),now(),now())",
                receiptId, TenantContext.tenantId(), cmd.projectId(), receiptNo, paymentId,
                payerName, total, "V" + receiptNo);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("paymentId", paymentId);
        out.put("paymentNo", "PY" + paymentId);
        out.put("receiptId", receiptId);
        out.put("receiptNo", receiptNo);
        out.put("amount", total);
        return out;
    }

    public List<Map<String, Object>> receipts(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select id, receipt_no receiptNo, payment_id paymentId, payer_name payerName, "
                        + "amount, receipt_status receiptStatus, issued_at issuedAt, pdf_url pdfUrl "
                        + "from prop_receipt where tenant_id=? and project_id=? order by id desc limit 200",
                TenantContext.tenantId(), projectId);
    }

    private void requireProject(Long projectId) {
        if (projectId == null) {
            throw BizException.paramInvalid("请选择项目");
        }
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) {
            throw BizException.notFound("物业项目");
        }
    }

    private static int months(LocalDate start, LocalDate end) {
        YearMonth a = YearMonth.from(start);
        YearMonth b = YearMonth.from(end);
        return (b.getYear() - a.getYear()) * 12 + b.getMonthValue() - a.getMonthValue() + 1;
    }

    private static String placeholders(int n) {
        return String.join(",", java.util.Collections.nCopies(n, "?"));
    }

    private static Object[] concat(Object[] prefix, List<Long> ids) {
        Object[] out = new Object[prefix.length + ids.size()];
        System.arraycopy(prefix, 0, out, 0, prefix.length);
        for (int i = 0; i < ids.size(); i++) out[prefix.length + i] = ids.get(i);
        return out;
    }

    private static String str(Object v) {
        return v == null ? null : String.valueOf(v);
    }

    public record FeeItemCmd(String feeItemCode, String feeItemName, String incomeCategory,
                             String incomeSubcategory, String chargeBasis, String billingCycle,
                             String unit, BigDecimal defaultPrice) {
    }

    public record GenerateCmd(Long projectId, Long feeItemId, LocalDate periodStart, LocalDate periodEnd) {
    }

    public record PayCmd(Long projectId, List<Long> billIds, BigDecimal payAmount,
                         String payChannel, String remark) {
    }
}
