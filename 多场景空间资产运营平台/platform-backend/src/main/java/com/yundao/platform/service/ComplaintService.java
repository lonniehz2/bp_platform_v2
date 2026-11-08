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
public class ComplaintService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public ComplaintService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId, String type) {
        String sql = "select c.id, c.project_id projectId, c.complaint_type complaintType, c.title, c.content, "
                + "c.house_id houseId, h.house_name houseName, c.person_id personId, p.person_name personName, "
                + "c.complaint_status complaintStatus, c.handler_name handlerName, c.handle_result handleResult, "
                + "c.create_time createTime from guarantee_complaint c "
                + "left join bp_house h on h.id=c.house_id left join bp_person p on p.id=c.person_id "
                + "where c.tenant_id=? and c.project_id=? and c.is_deleted=0 ";
        if (type != null && !type.isBlank()) {
            return jdbc.queryForList(sql + "and c.complaint_type=? order by c.id desc",
                    TenantContext.require(), projectId, type);
        }
        return jdbc.queryForList(sql + "order by c.id desc", TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        if (cmd.projectId() == null || cmd.title() == null || cmd.title().isBlank()) {
            throw BizException.param("项目和标题不能为空");
        }
        String type = cmd.complaintType() == null ? "COMPLAINT" : cmd.complaintType();
        if (!List.of("COMPLAINT", "APPEAL", "VISIT").contains(type)) {
            throw BizException.param("类型不合法");
        }
        long id = idGen.nextId();
        jdbc.update("insert into guarantee_complaint(id,tenant_id,project_id,complaint_type,title,content,"
                        + "house_id,person_id,complaint_status,is_deleted) values(?,?,?,?,?,?,?,?, 'PENDING',0)",
                id, TenantContext.require(), cmd.projectId(), type, cmd.title().trim(),
                cmd.content(), cmd.houseId(), cmd.personId());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("complaintType", type);
        out.put("complaintStatus", "PENDING");
        return out;
    }

    public Map<String, Object> handle(long id, HandleCmd cmd) {
        if (cmd.complaintStatus() != null
                && !List.of("PENDING", "PROCESSING", "RESOLVED", "CLOSED").contains(cmd.complaintStatus())) {
            throw BizException.param("状态不合法");
        }
        long updated = jdbc.update("update guarantee_complaint set complaint_status=coalesce(?,complaint_status), "
                        + "handler_name=coalesce(?,handler_name), handle_result=coalesce(?,handle_result), "
                        + "update_time=now() where id=? and tenant_id=? and is_deleted=0",
                cmd.complaintStatus(), cmd.handlerName(), cmd.handleResult(), id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("投诉记录不存在");
        }
        return Map.of("id", id, "complaintStatus",
                cmd.complaintStatus() == null ? "UNCHANGED" : cmd.complaintStatus());
    }

    public record CreateCmd(Long projectId, String complaintType, String title, String content,
                            Long houseId, Long personId) {
    }

    public record HandleCmd(String complaintStatus, String handlerName, String handleResult) {
    }
}
