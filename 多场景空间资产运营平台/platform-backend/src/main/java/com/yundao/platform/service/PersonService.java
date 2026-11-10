package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class PersonService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final DataScopeService dataScope;

    public PersonService(JdbcTemplate jdbc, IdGenerator idGen, DataScopeService dataScope) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.dataScope = dataScope;
    }

    public List<Map<String, Object>> list(String keyword, String personType) {
        String like = keyword == null || keyword.isBlank() ? null : "%" + keyword.trim() + "%";
        Set<Long> projectIds = dataScope.projectIds();
        if (projectIds != null && projectIds.isEmpty()) {
            return List.of();
        }
        String scopeSql = "";
        List<Object> params = new ArrayList<>();
        params.add(TenantContext.require());
        params.add(like); params.add(like); params.add(like); params.add(like);
        params.add(personType); params.add(personType);
        if (projectIds != null) {
            scopeSql = " and exists (select 1 from bp_person_relation r "
                    + "where r.person_id=p.id and r.is_deleted=0 and r.project_id in ("
                    + String.join(",", Collections.nCopies(projectIds.size(), "?")) + "))";
            params.addAll(projectIds);
        }
        return jdbc.queryForList(
                "select p.id, p.person_code personCode, p.person_name personName, p.phone, "
                        + "p.id_card_mask idCardMask, p.person_type personType, p.verify_status verifyStatus, p.status, "
                        + "p.gender, p.birth_date birthDate, p.address, p.employer, p.emergency_contact emergencyContact, p.remark "
                        + "from bp_person p where p.tenant_id=? and p.is_deleted=0 "
                        + "and (? is null or p.person_name like ? or p.person_code like ? or p.phone like ?) "
                        + "and (? is null or p.person_type=?)" + scopeSql + " order by p.id desc",
                params.toArray());
    }

    public Map<String, Object> create(PersonCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.personCode() == null || cmd.personCode().isBlank()
                || cmd.personName() == null || cmd.personName().isBlank()) {
            throw BizException.param("人员编码和姓名不能为空");
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into bp_person(id,tenant_id,person_code,person_name,phone,"
                            + "id_card_mask,person_type,gender,birth_date,address,employer,emergency_contact,remark,"
                            + "status,is_deleted) values(?,?,?,?,?,?,?,?,?,?,?,?,?,'ENABLED',0)",
                    id, tenant, cmd.personCode().trim(), cmd.personName().trim(), cmd.phone(),
                    cmd.idCardMask(), cmd.personType(), cmd.gender(), cmd.birthDate(), cmd.address(),
                    cmd.employer(), cmd.emergencyContact(), cmd.remark());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("人员编码已存在");
        }
        return Map.of("id", id, "personCode", cmd.personCode(), "personName", cmd.personName());
    }



    public Map<String, Object> archive(long personId) {
        String tenant = TenantContext.require();
        Long contracts = jdbc.queryForObject("select count(*) from guarantee_contract where person_id=? and is_deleted=0 "
                + "and contract_status in ('ACTIVE','APPROVING','DRAFT')", Long.class, personId);
        if (contracts != null && contracts > 0) throw BizException.conflict("人员存在合同，不能归档");
        int updated = jdbc.update("update bp_person set is_deleted=1, update_time=now() "
                + "where id=? and tenant_id=? and is_deleted=0", personId, tenant);
        if (updated == 0) throw BizException.notFound("人员不存在");
        return Map.of("id", personId, "archived", true);
    }

    public Map<String, Object> update(long personId, PersonCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.personName() == null || cmd.personName().isBlank()) {
            throw BizException.param("姓名不能为空");
        }
        int updated = jdbc.update("update bp_person set person_name=?, phone=?, id_card_mask=?, person_type=?, "
                        + "gender=?, birth_date=?, address=?, employer=?, emergency_contact=?, remark=?, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                cmd.personName().trim(), cmd.phone(), cmd.idCardMask(), cmd.personType(), cmd.gender(),
                cmd.birthDate(), cmd.address(), cmd.employer(), cmd.emergencyContact(), cmd.remark(),
                personId, tenant);
        if (updated == 0) throw BizException.notFound("人员不存在");
        return Map.of("id", personId, "personName", cmd.personName());
    }

    public Map<String, Object> setStatus(long personId, String status) {
        if (!List.of("ENABLED", "DISABLED").contains(status)) throw BizException.param("状态不合法");
        int updated = jdbc.update("update bp_person set status=?, update_time=now() "
                + "where id=? and tenant_id=? and is_deleted=0", status, personId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("人员不存在");
        return Map.of("id", personId, "status", status);
    }

    public List<Map<String, Object>> relations(long personId) {
        requirePerson(personId);
        return jdbc.queryForList(
                "select r.id, r.project_id projectId, r.target_type targetType, r.target_id targetId, "
                        + "r.relation_type relationType, r.is_primary isPrimary, r.start_date startDate, "
                        + "r.end_date endDate, r.status, "
                        + "case r.target_type when 'HOUSE' then h.house_name when 'SPACE' then s.space_name "
                        + "else o.org_name end targetName "
                        + "from bp_person_relation r "
                        + "left join bp_house h on r.target_type='HOUSE' and h.id=r.target_id "
                        + "left join bp_space s on r.target_type='SPACE' and s.id=r.target_id "
                        + "left join bp_org o on r.target_type='PROJECT' and o.id=r.target_id "
                        + "where r.tenant_id=? and r.person_id=? and r.is_deleted=0 order by r.id desc",
                TenantContext.require(), personId);
    }

    public Map<String, Object> createRelation(long personId, RelationCmd cmd) {
        String tenant = TenantContext.require();
        requirePerson(personId);
        if (cmd.projectId() == null || cmd.targetType() == null || cmd.targetId() == null
                || cmd.relationType() == null || cmd.relationType().isBlank()) {
            throw BizException.param("项目、关联对象和关系类型不能为空");
        }
        requireProject(cmd.projectId());
        boolean targetOk = switch (cmd.targetType()) {
            case "PROJECT" -> cmd.targetId().equals(cmd.projectId());
            case "HOUSE" -> count("select count(*) from bp_house where id=? and tenant_id=? and org_id=? "
                    + "and is_deleted=0", cmd.targetId(), tenant, cmd.projectId()) > 0;
            case "SPACE" -> count("select count(*) from bp_space where id=? and tenant_id=? and org_id=? "
                    + "and is_deleted=0", cmd.targetId(), tenant, cmd.projectId()) > 0;
            default -> false;
        };
        if (!targetOk) {
            throw BizException.param("关联对象不属于当前项目");
        }
        if (cmd.startDate() != null && cmd.endDate() != null && cmd.endDate().isBefore(cmd.startDate())) {
            throw BizException.param("结束日期不能早于开始日期");
        }
        long id = idGen.nextId();
        jdbc.update("insert into bp_person_relation(id,tenant_id,person_id,project_id,target_type,target_id,"
                        + "relation_type,is_primary,start_date,end_date,status,is_deleted) "
                        + "values(?,?,?,?,?,?,?,?,?,?, 'ACTIVE',0)",
                id, tenant, personId, cmd.projectId(), cmd.targetType(), cmd.targetId(),
                cmd.relationType().trim(), Boolean.TRUE.equals(cmd.isPrimary()) ? 1 : 0,
                cmd.startDate(), cmd.endDate());
        return Map.of("id", id, "personId", personId, "relationType", cmd.relationType());
    }


    public Map<String, Object> removeRelation(long personId, long relationId) {
        int updated = jdbc.update("update bp_person_relation set is_deleted=1, status='ENDED', "
                        + "update_time=now() where id=? and person_id=? and tenant_id=? and is_deleted=0",
                relationId, personId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("人员关系不存在");
        return Map.of("id", relationId, "status", "ENDED");
    }

    private void requirePerson(long personId) {
        if (count("select count(*) from bp_person where id=? and tenant_id=? and is_deleted=0",
                personId, TenantContext.require()) == 0) {
            throw BizException.notFound("人员不存在");
        }
    }

    private void requireProject(long projectId) {
        if (count("select count(*) from bp_org where id=? and tenant_id=? and is_deleted=0",
                projectId, TenantContext.require()) == 0) {
            throw BizException.notFound("项目不存在");
        }
    }

    private long count(String sql, Object... args) {
        Long value = jdbc.queryForObject(sql, Long.class, args);
        return value == null ? 0 : value;
    }

    public record PersonCmd(String personCode, String personName, String phone,
                            String idCardMask, String personType, String gender,
                            LocalDate birthDate, String address, String employer,
                            String emergencyContact, String remark) {
    }

    public record RelationCmd(Long projectId, String targetType, Long targetId, String relationType,
                              Boolean isPrimary, LocalDate startDate, LocalDate endDate) {
    }
}
