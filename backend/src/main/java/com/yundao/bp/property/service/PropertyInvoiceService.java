package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 电子发票申请。第一版保存申请并模拟开票，真实税控/发票平台后续接入。 */
@Service
public class PropertyInvoiceService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;
    private final InvoiceGateway invoiceGateway;

    public PropertyInvoiceService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen,
                                  InvoiceGateway invoiceGateway) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.invoiceGateway = invoiceGateway;
    }

    public List<Map<String, Object>> list(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select i.id, i.receipt_id receiptId, r.receipt_no receiptNo, i.invoice_no invoiceNo, "
                        + "i.invoice_title invoiceTitle, i.tax_no taxNo, i.email, i.amount, "
                        + "i.invoice_status invoiceStatus, i.invoice_url invoiceUrl, i.requested_at requestedAt, "
                        + "i.issued_at issuedAt from prop_invoice i left join prop_receipt r on r.id=i.receipt_id "
                        + "where i.tenant_id=? and i.project_id=? order by i.id desc limit 200",
                TenantContext.tenantId(), projectId);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> request(Long projectId, InvoiceCmd cmd) {
        requireProject(projectId);
        List<Map<String, Object>> receipts = jdbc.queryForList(
                "select amount from prop_receipt where id=? and tenant_id=? and project_id=? and receipt_status='ISSUED'",
                cmd.receiptId(), TenantContext.tenantId(), projectId);
        if (receipts.isEmpty()) throw BizException.notFound("可开票的电子收据");
        Long dup = jdbc.queryForObject("select count(*) from prop_invoice where tenant_id=? and receipt_id=? "
                        + "and invoice_status in ('PENDING','ISSUED')",
                Long.class, TenantContext.tenantId(), cmd.receiptId());
        if (dup != null && dup > 0) throw BizException.stateConflict("该收据已申请开票");
        long id = idGen.nextId();
        BigDecimal amount = (BigDecimal) receipts.get(0).get("amount");
        jdbc.update("insert into prop_invoice(id,tenant_id,project_id,receipt_id,invoice_title,tax_no,email,"
                        + "amount,invoice_status,requested_at,create_by,create_time,update_time) "
                        + "values(?,?,?,?,?,?,?,?, 'PENDING',now(),?,now(),now())",
                id, TenantContext.tenantId(), projectId, cmd.receiptId(), cmd.invoiceTitle(),
                cmd.taxNo(), cmd.email(), amount, String.valueOf(TenantContext.userId()));
        return Map.of("id", id);
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> issue(Long id) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select i.id, i.invoice_title, i.tax_no, i.email, i.amount, r.receipt_no "
                        + "from prop_invoice i left join prop_receipt r on r.id=i.receipt_id "
                        + "where i.id=? and i.tenant_id=? and i.invoice_status='PENDING'",
                id, TenantContext.tenantId());
        if (rows.isEmpty()) throw BizException.notFound("待开票申请");
        Map<String, Object> row = rows.get(0);
        InvoiceGateway.IssueResult result = invoiceGateway.issue(new InvoiceGateway.IssueRequest(
                id, String.valueOf(row.get("receipt_no")), String.valueOf(row.get("invoice_title")),
                row.get("tax_no") == null ? null : String.valueOf(row.get("tax_no")),
                row.get("email") == null ? null : String.valueOf(row.get("email")),
                (BigDecimal) row.get("amount")));
        if (!result.success()) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.SYSTEM_ERROR,
                    "开票失败：" + result.error());
        }
        String invoiceNo = result.invoiceNo() == null ? "FP" + id : result.invoiceNo();
        jdbc.update("update prop_invoice set invoice_no=?, invoice_url=?, invoice_status='ISSUED', "
                        + "issued_at=now(), update_time=now() where id=?",
                invoiceNo, result.invoiceUrl(), id);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("invoiceNo", invoiceNo);
        out.put("invoiceUrl", result.invoiceUrl());
        out.put("status", "ISSUED");
        return out;
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }

    public record InvoiceCmd(Long receiptId, String invoiceTitle, String taxNo, String email) {
    }
}
