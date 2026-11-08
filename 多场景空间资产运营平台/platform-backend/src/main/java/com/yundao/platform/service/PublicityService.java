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
public class PublicityService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public PublicityService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select id, project_id projectId, publicity_type publicityType, title, content, "
                        + "start_date startDate, end_date endDate, publicity_status publicityStatus, create_time createTime "
                        + "from guarantee_publicity where tenant_id=? and project_id=? and is_deleted=0 "
                        + "order by id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        if (cmd.projectId() == null || cmd.title() == null || cmd.title().isBlank()) {
            throw BizException.param("项目和标题不能为空");
        }
        String type = cmd.publicityType() == null ? "ALLOCATION" : cmd.publicityType();
        if (!List.of("ALLOCATION", "QUALIFICATION", "EXIT", "POLICY").contains(type)) {
            throw BizException.param("公示类型不合法");
        }
        long id = idGen.nextId();
        jdbc.update("insert into guarantee_publicity(id,tenant_id,project_id,publicity_type,title,content,"
                        + "start_date,end_date,publicity_status,is_deleted) values(?,?,?,?,?,?,?,?, 'DRAFT',0)",
                id, TenantContext.require(), cmd.projectId(), type, cmd.title().trim(), cmd.content(),
                cmd.startDate(), cmd.endDate());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("title", cmd.title());
        out.put("publicityStatus", "DRAFT");
        return out;
    }

    public Map<String, Object> updateStatus(long id, String status) {
        if (!List.of("PUBLISHED", "CLOSED").contains(status)) {
            throw BizException.param("公示状态不合法");
        }
        long updated = jdbc.update("update guarantee_publicity set publicity_status=?, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                status, id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("公示不存在");
        }
        return Map.of("id", id, "publicityStatus", status);
    }

    public record CreateCmd(Long projectId, String publicityType, String title, String content,
                            LocalDate startDate, LocalDate endDate) {
    }
}
