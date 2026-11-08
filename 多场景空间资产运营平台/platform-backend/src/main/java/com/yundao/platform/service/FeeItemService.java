package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class FeeItemService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public FeeItemService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select id, project_id projectId, fee_code feeCode, fee_name feeName, fee_type feeType, "
                        + "billing_cycle billingCycle, unit_price unitPrice, unit_name unitName, "
                        + "tax_rate taxRate, fee_status feeStatus "
                        + "from guarantee_fee_item where tenant_id=? and project_id=? and is_deleted=0 "
                        + "order by fee_type, fee_code",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        if (cmd.projectId() == null || cmd.feeCode() == null || cmd.feeCode().isBlank()
                || cmd.feeName() == null || cmd.feeName().isBlank()) {
            throw BizException.param("项目、费用编码、费用名称不能为空");
        }
        String type = cmd.feeType() == null ? "OTHER" : cmd.feeType();
        if (!List.of("RENT", "DEPOSIT", "WATER", "ELECTRICITY", "GAS", "SERVICE", "OTHER").contains(type)) {
            throw BizException.param("费用类型不合法");
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_fee_item(id,tenant_id,project_id,fee_code,fee_name,fee_type,"
                            + "billing_cycle,unit_price,unit_name,tax_rate,fee_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?, 'ENABLED',0)",
                    id, TenantContext.require(), cmd.projectId(), cmd.feeCode().trim(), cmd.feeName().trim(),
                    type, cmd.billingCycle() == null ? "MONTHLY" : cmd.billingCycle(),
                    cmd.unitPrice() == null ? BigDecimal.ZERO : cmd.unitPrice(),
                    cmd.unitName(), cmd.taxRate() == null ? BigDecimal.ZERO : cmd.taxRate());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("同一项目费用编码不能重复");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("feeCode", cmd.feeCode());
        out.put("feeStatus", "ENABLED");
        return out;
    }

    public Map<String, Object> toggle(long id, boolean enabled) {
        long updated = jdbc.update("update guarantee_fee_item set fee_status=?, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                enabled ? "ENABLED" : "DISABLED", id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("计费项目不存在");
        }
        return Map.of("id", id, "feeStatus", enabled ? "ENABLED" : "DISABLED");
    }

    public record CreateCmd(Long projectId, String feeCode, String feeName, String feeType,
                            String billingCycle, BigDecimal unitPrice, String unitName, BigDecimal taxRate) {
    }
}
