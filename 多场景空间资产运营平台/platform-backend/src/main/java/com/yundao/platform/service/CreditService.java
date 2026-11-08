package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class CreditService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public CreditService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select c.id, c.project_id projectId, c.person_id personId, p.person_name personName, "
                        + "c.credit_type creditType, c.score_change scoreChange, c.reason, c.record_status recordStatus, "
                        + "c.effective_date effectiveDate, c.expire_date expireDate, c.create_time createTime "
                        + "from guarantee_credit_record c left join bp_person p on p.id=c.person_id "
                        + "where c.tenant_id=? and c.project_id=? and c.is_deleted=0 order by c.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        if (cmd.projectId() == null || cmd.personId() == null) {
            throw BizException.param("项目和人员不能为空");
        }
        String type = cmd.creditType() == null ? "VIOLATION" : cmd.creditType();
        if (!List.of("VIOLATION", "ARREARS", "OTHER").contains(type)) {
            throw BizException.param("信用类型不合法");
        }
        long id = idGen.nextId();
        jdbc.update("insert into guarantee_credit_record(id,tenant_id,project_id,person_id,credit_type,"
                        + "score_change,reason,record_status,effective_date,expire_date,is_deleted) "
                        + "values(?,?,?,?,?,?,?, 'ACTIVE',?,?,0)",
                id, TenantContext.require(), cmd.projectId(), cmd.personId(), type,
                cmd.scoreChange() == null ? 0 : cmd.scoreChange(), cmd.reason(),
                cmd.effectiveDate() == null ? LocalDate.now() : cmd.effectiveDate(), cmd.expireDate());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("recordStatus", "ACTIVE");
        return out;
    }

    public Map<String, Object> revoke(long id) {
        long updated = jdbc.update("update guarantee_credit_record set record_status='REVOKED', update_time=now() "
                        + "where id=? and tenant_id=? and record_status='ACTIVE' and is_deleted=0",
                id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("信用记录不存在或已撤销");
        }
        return Map.of("id", id, "recordStatus", "REVOKED");
    }

    public record CreateCmd(Long projectId, Long personId, String creditType, Integer scoreChange,
                            String reason, LocalDate effectiveDate, LocalDate expireDate) {
    }
}
