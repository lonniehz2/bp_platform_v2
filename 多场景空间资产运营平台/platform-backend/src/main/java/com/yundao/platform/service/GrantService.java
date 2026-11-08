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
public class GrantService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public GrantService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long personId, Long projectId) {
        return jdbc.queryForList(
                "select g.id, g.project_id projectId, g.person_id personId, g.target_type targetType, "
                        + "g.target_id targetId, g.grant_level grantLevel, g.valid_start validStart, "
                        + "g.valid_end validEnd, g.grant_status grantStatus, g.source_type sourceType, "
                        + "g.source_id sourceId from bp_grant_entitlement g "
                        + "where g.tenant_id=? and g.person_id=? and (? is null or g.project_id=?) "
                        + "and g.is_deleted=0 order by g.id desc",
                TenantContext.require(), personId, projectId, projectId);
    }

    public Map<String, Object> create(GrantCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.personId() == null || cmd.projectId() == null || cmd.targetType() == null
                || cmd.targetId() == null) {
            throw BizException.param("人员、项目、授权对象不能为空");
        }
        if (count("select count(*) from bp_person where id=? and tenant_id=? and is_deleted=0",
                cmd.personId(), tenant) == 0) {
            throw BizException.param("人员不存在");
        }
        requireProject(cmd.projectId());
        boolean targetOk = switch (cmd.targetType()) {
            case "SPACE" -> count("select count(*) from bp_space where id=? and tenant_id=? and org_id=? "
                    + "and is_deleted=0", cmd.targetId(), tenant, cmd.projectId()) > 0;
            case "DEVICE" -> count("select count(*) from bp_dev_device where id=? and tenant_id=? and project_id=? "
                    + "and is_deleted=0", cmd.targetId(), tenant, cmd.projectId()) > 0;
            default -> false;
        };
        if (!targetOk) {
            throw BizException.param("授权对象不属于当前项目");
        }
        LocalDate start = cmd.validStart() == null ? LocalDate.now() : cmd.validStart();
        if (cmd.validEnd() != null && cmd.validEnd().isBefore(start)) {
            throw BizException.param("授权结束日期不能早于开始日期");
        }
        long duplicate = count("select count(*) from bp_grant_entitlement where tenant_id=? and person_id=? "
                        + "and target_type=? and target_id=? and grant_status='ACTIVE' and is_deleted=0",
                tenant, cmd.personId(), cmd.targetType(), cmd.targetId());
        if (duplicate > 0) {
            throw BizException.conflict("该人员已存在有效授权");
        }
        long id = idGen.nextId();
        jdbc.update("insert into bp_grant_entitlement(id,tenant_id,project_id,person_id,target_type,target_id,"
                        + "grant_level,valid_start,valid_end,grant_status,source_type,source_id,is_deleted) "
                        + "values(?,?,?,?,?,?,?,?,?, 'ACTIVE',?,?,0)",
                id, tenant, cmd.projectId(), cmd.personId(), cmd.targetType(), cmd.targetId(),
                cmd.grantLevel() == null ? "OPEN" : cmd.grantLevel(), start, cmd.validEnd(),
                cmd.sourceType(), cmd.sourceId());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("personId", cmd.personId());
        out.put("targetType", cmd.targetType());
        out.put("targetId", cmd.targetId());
        out.put("grantStatus", "ACTIVE");
        return out;
    }

    public List<Map<String, Object>> keyring(long personId) {
        return jdbc.queryForList(
                "select g.id, g.project_id projectId, g.target_type targetType, g.target_id targetId, "
                        + "g.grant_level grantLevel, g.valid_start validStart, g.valid_end validEnd, "
                        + "case g.target_type when 'SPACE' then s.space_name when 'DEVICE' then d.device_name "
                        + "else null end targetName "
                        + "from bp_grant_entitlement g "
                        + "left join bp_space s on g.target_type='SPACE' and s.id=g.target_id "
                        + "left join bp_dev_device d on g.target_type='DEVICE' and d.id=g.target_id "
                        + "where g.tenant_id=? and g.person_id=? and g.grant_status='ACTIVE' "
                        + "and g.valid_start<=curdate() and (g.valid_end is null or g.valid_end>=curdate()) "
                        + "and g.is_deleted=0 order by g.id",
                TenantContext.require(), personId);
    }

    public Map<String, Object> revoke(long grantId, String reason) {
        long updated = jdbc.update("update bp_grant_entitlement set grant_status='REVOKED', revoke_reason=?, "
                        + "update_time=now() where id=? and tenant_id=? and grant_status='ACTIVE' and is_deleted=0",
                reason, grantId, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("有效授权不存在");
        }
        return Map.of("id", grantId, "grantStatus", "REVOKED");
    }

    private void requireProject(long projectId) {
        if (count("select count(*) from bp_org where id=? and tenant_id=? and is_deleted=0",
                projectId, TenantContext.require()) == 0) {
            throw BizException.param("项目不存在");
        }
    }

    private long count(String sql, Object... args) {
        Long value = jdbc.queryForObject(sql, Long.class, args);
        return value == null ? 0 : value;
    }

    public record GrantCmd(Long projectId, Long personId, String targetType, Long targetId,
                           String grantLevel, LocalDate validStart, LocalDate validEnd,
                           String sourceType, Long sourceId) {
    }
}
