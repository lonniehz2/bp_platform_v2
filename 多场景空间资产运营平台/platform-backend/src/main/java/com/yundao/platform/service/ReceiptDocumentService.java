package com.yundao.platform.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReceiptDocumentService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final ObjectMapper json;

    public ReceiptDocumentService(JdbcTemplate jdbc, IdGenerator idGen, ObjectMapper json) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.json = json;
    }

    @Transactional
    public Map<String, Object> getOrCreate(long receiptId, long projectId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, verify_token token, verify_code code, template_id templateId, template_version templateVersion " +
                        "from bp_receipt_document where tenant_id=? and receipt_id=? and is_deleted=0",
                tenant, receiptId);
        Map<String, Object> template = activeTemplate(tenant);
        if (!rows.isEmpty()) {
            Map<String, Object> row = rows.get(0);
            if (String.valueOf(row.get("templateId")).equals(String.valueOf(template.get("id")))
                    && String.valueOf(row.get("templateVersion")).equals(String.valueOf(template.get("version")))) {
                return row;
            }
            jdbc.update("update bp_receipt_document set template_id=?, template_version=? where id=?",
                    template.get("id"), template.get("version"), row.get("id"));
            row.put("templateId", template.get("id"));
            row.put("templateVersion", template.get("version"));
            return row;
        }
        String token = UUID.randomUUID().toString().replace("-", "");
        String code = token.substring(0, 8).toUpperCase();
        long id = idGen.nextId();
        jdbc.update("insert into bp_receipt_document(id,tenant_id,receipt_id,project_id,template_id,template_version," +
                        "verify_token,verify_code,document_status,is_deleted) values(?,?,?,?,?,?,?,?,'VALID',0)",
                id, tenant, receiptId, projectId, template.get("id"), template.get("version"), token, code);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("token", token);
        out.put("code", code);
        out.put("templateId", template.get("id"));
        out.put("templateVersion", template.get("version"));
        return out;
    }

    public Map<String, Object> config(long templateId) {
        try {
            List<Map<String, Object>> rows = jdbc.queryForList(
                    "select config_json configJson from bp_receipt_template where id=? and is_deleted=0", templateId);
            if (rows.isEmpty()) return Map.of();
            Object raw = rows.get(0).get("configJson");
            if (raw == null) return Map.of();
            return json.readValue(String.valueOf(raw), Map.class);
        } catch (Exception e) {
            return Map.of();
        }
    }

    private Map<String, Object> activeTemplate(String tenant) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, version from bp_receipt_template where tenant_id=? and status='PUBLISHED' and is_deleted=0 " +
                        "order by version desc limit 1", tenant);
        if (!rows.isEmpty()) return rows.get(0);
        return Map.of("id", 0, "version", 1);
    }

    public Map<String, Object> verify(String token) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select d.verify_code verifyCode, d.document_status documentStatus, d.create_time createTime, " +
                        "r.receipt_no receiptNo, r.amount amount, r.issued_time issuedTime, p.payment_no paymentNo " +
                        "from bp_receipt_document d join bp_receipt r on r.id=d.receipt_id " +
                        "join bp_payment p on p.id=r.payment_id where d.verify_token=? and d.is_deleted=0", token);
        if (rows.isEmpty()) return Map.of("valid", false, "status", "NOT_FOUND");
        Map<String, Object> row = rows.get(0);
        boolean valid = "VALID".equals(String.valueOf(row.get("documentStatus")));
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("valid", valid);
        out.put("status", row.get("documentStatus"));
        out.put("receiptNo", row.get("receiptNo"));
        out.put("paymentNo", row.get("paymentNo"));
        out.put("amount", row.get("amount"));
        out.put("issuedTime", row.get("issuedTime"));
        out.put("verifyCode", row.get("verifyCode"));
        return out;
    }

    public void savePdfHash(long receiptId, String hash) {
        jdbc.update("update bp_receipt_document set pdf_sha256=? where tenant_id=? and receipt_id=? and is_deleted=0", hash, TenantContext.require(), receiptId);
    }

    public void markStatus(long receiptId, String status) {
        jdbc.update("update bp_receipt_document set document_status=? where tenant_id=? and receipt_id=? and is_deleted=0",
                status, TenantContext.require(), receiptId);
    }
}
