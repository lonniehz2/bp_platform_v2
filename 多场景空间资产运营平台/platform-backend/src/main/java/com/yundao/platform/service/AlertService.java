package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class AlertService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public AlertService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select a.id, a.project_id projectId, a.alert_type alertType, a.alert_level alertLevel, "
                        + "a.title, a.content, a.house_id houseId, h.house_name houseName, a.person_id personId, "
                        + "p.person_name personName, a.alert_status alertStatus, a.handler_name handlerName, "
                        + "a.handle_result handleResult, a.create_time createTime "
                        + "from guarantee_alert a left join bp_house h on h.id=a.house_id "
                        + "left join bp_person p on p.id=a.person_id "
                        + "where a.tenant_id=? and a.project_id=? and a.is_deleted=0 order by a.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        if (cmd.projectId() == null || cmd.title() == null || cmd.title().isBlank()) {
            throw BizException.param("项目和标题不能为空");
        }
        long id = idGen.nextId();
        jdbc.update("insert into guarantee_alert(id,tenant_id,project_id,alert_type,alert_level,title,content,"
                        + "house_id,person_id,alert_status,is_deleted) values(?,?,?,?,?,?,?,?,?, 'PENDING',0)",
                id, TenantContext.require(), cmd.projectId(),
                cmd.alertType() == null ? "RISK" : cmd.alertType(),
                cmd.alertLevel() == null ? "NORMAL" : cmd.alertLevel(),
                cmd.title().trim(), cmd.content(), cmd.houseId(), cmd.personId());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("alertStatus", "PENDING");
        return out;
    }

    public Map<String, Object> handle(long id, HandleCmd cmd) {
        if (cmd.alertStatus() != null
                && !List.of("PENDING", "PROCESSING", "RESOLVED", "IGNORED").contains(cmd.alertStatus())) {
            throw BizException.param("告警状态不合法");
        }
        long updated = jdbc.update("update guarantee_alert set alert_status=coalesce(?,alert_status), "
                        + "handler_name=coalesce(?,handler_name), handle_result=coalesce(?,handle_result), "
                        + "update_time=now() where id=? and tenant_id=? and is_deleted=0",
                cmd.alertStatus(), cmd.handlerName(), cmd.handleResult(), id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("告警不存在");
        }
        return Map.of("id", id, "alertStatus",
                cmd.alertStatus() == null ? "UNCHANGED" : cmd.alertStatus());
    }

    public record CreateCmd(Long projectId, String alertType, String alertLevel, String title,
                            String content, Long houseId, Long personId) {
    }

    public record HandleCmd(String alertStatus, String handlerName, String handleResult) {
    }
}
