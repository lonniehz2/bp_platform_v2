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
public class CohabitantService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public CohabitantService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long contractId) {
        requireContract(contractId);
        return jdbc.queryForList(
                "select c.id, c.contract_id contractId, c.person_id personId, p.person_name personName, "
                        + "p.person_code personCode, c.relation_type relationType, c.is_primary isPrimary, "
                        + "c.start_date startDate, c.end_date endDate, c.cohabitant_status cohabitantStatus, "
                        + "c.remark, c.create_time createTime from guarantee_contract_cohabitant c "
                        + "left join bp_person p on p.id=c.person_id "
                        + "where c.tenant_id=? and c.contract_id=? and c.is_deleted=0 order by c.id",
                TenantContext.require(), contractId);
    }

    public Map<String, Object> add(long contractId, AddCmd cmd) {
        String tenant = TenantContext.require();
        requireContract(contractId);
        if (cmd.personId() == null) {
            throw BizException.param("人员不能为空");
        }
        Long person = jdbc.queryForObject(
                "select count(*) from bp_person where id=? and tenant_id=? and is_deleted=0",
                Long.class, cmd.personId(), tenant);
        if (person == null || person == 0) {
            throw BizException.param("人员不存在");
        }
        Long exists = jdbc.queryForObject(
                "select count(*) from guarantee_contract_cohabitant where tenant_id=? and contract_id=? "
                        + "and person_id=? and cohabitant_status='ACTIVE' and is_deleted=0",
                Long.class, tenant, contractId, cmd.personId());
        if (exists != null && exists > 0) {
            throw BizException.conflict("该人员已是合同同住人");
        }
        long id = idGen.nextId();
        jdbc.update("insert into guarantee_contract_cohabitant(id,tenant_id,contract_id,person_id,relation_type,"
                        + "is_primary,start_date,end_date,cohabitant_status,remark,is_deleted) "
                        + "values(?,?,?,?,?,?,?,?, 'ACTIVE',?,0)",
                id, tenant, contractId, cmd.personId(),
                cmd.relationType() == null ? "FAMILY" : cmd.relationType(),
                Boolean.TRUE.equals(cmd.isPrimary()) ? 1 : 0,
                cmd.startDate(), cmd.endDate(), cmd.remark());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("contractId", contractId);
        out.put("personId", cmd.personId());
        out.put("cohabitantStatus", "ACTIVE");
        return out;
    }

    public Map<String, Object> remove(long id) {
        long updated = jdbc.update("update guarantee_contract_cohabitant set cohabitant_status='REMOVED', "
                        + "is_deleted=1, update_time=now() where id=? and tenant_id=? and is_deleted=0",
                id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("同住人记录不存在");
        }
        return Map.of("id", id, "cohabitantStatus", "REMOVED");
    }

    private void requireContract(long contractId) {
        Long count = jdbc.queryForObject(
                "select count(*) from guarantee_contract where id=? and tenant_id=? and is_deleted=0",
                Long.class, contractId, TenantContext.require());
        if (count == null || count == 0) {
            throw BizException.notFound("合同不存在");
        }
    }

    public record AddCmd(Long personId, String relationType, Boolean isPrimary,
                         LocalDate startDate, LocalDate endDate, String remark) {
    }
}
