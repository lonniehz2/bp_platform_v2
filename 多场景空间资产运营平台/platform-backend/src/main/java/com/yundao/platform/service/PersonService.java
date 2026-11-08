package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class PersonService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public PersonService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(String keyword, String personType) {
        String like = keyword == null || keyword.isBlank() ? null : "%" + keyword.trim() + "%";
        return jdbc.queryForList(
                "select id, person_code personCode, person_name personName, phone, "
                        + "id_card_mask idCardMask, person_type personType, verify_status verifyStatus, status "
                        + "from bp_person where tenant_id=? and is_deleted=0 "
                        + "and (? is null or person_name like ? or person_code like ? or phone like ?) "
                        + "and (? is null or person_type=?) order by id desc",
                TenantContext.require(), like, like, like, like, personType, personType);
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
                            + "id_card_mask,person_type,status,is_deleted) values(?,?,?,?,?,?,?,'ENABLED',0)",
                    id, tenant, cmd.personCode().trim(), cmd.personName().trim(), cmd.phone(),
                    cmd.idCardMask(), cmd.personType());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("人员编码已存在");
        }
        return Map.of("id", id, "personCode", cmd.personCode(), "personName", cmd.personName());
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
                            String idCardMask, String personType) {
    }

    public record RelationCmd(Long projectId, String targetType, Long targetId, String relationType,
                              Boolean isPrimary, LocalDate startDate, LocalDate endDate) {
    }
}
