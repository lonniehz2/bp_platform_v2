package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class AccessRecordService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public AccessRecordService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select a.id, a.project_id projectId, a.house_id houseId, h.house_name houseName, "
                        + "a.person_id personId, p.person_name personName, a.visitor_name visitorName, "
                        + "a.visitor_phone visitorPhone, a.purpose, a.valid_start validStart, a.valid_end validEnd, "
                        + "a.access_status accessStatus, a.create_time createTime "
                        + "from guarantee_access_record a left join bp_house h on h.id=a.house_id "
                        + "left join bp_person p on p.id=a.person_id "
                        + "where a.tenant_id=? and a.project_id=? and a.is_deleted=0 order by a.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        if (cmd.projectId() == null || cmd.visitorName() == null || cmd.visitorName().isBlank()) {
            throw BizException.param("项目和访客姓名不能为空");
        }
        long id = idGen.nextId();
        jdbc.update("insert into guarantee_access_record(id,tenant_id,project_id,house_id,person_id,"
                        + "visitor_name,visitor_phone,purpose,valid_start,valid_end,access_status,is_deleted) "
                        + "values(?,?,?,?,?,?,?,?,?,?, 'PENDING',0)",
                id, TenantContext.require(), cmd.projectId(), cmd.houseId(), cmd.personId(),
                cmd.visitorName().trim(), cmd.visitorPhone(), cmd.purpose(),
                cmd.validStart(), cmd.validEnd());
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("visitorName", cmd.visitorName());
        out.put("accessStatus", "PENDING");
        return out;
    }

    public Map<String, Object> approve(long id, String status) {
        if (!List.of("APPROVED", "REJECTED").contains(status)) {
            throw BizException.param("审批状态不合法");
        }
        long updated = jdbc.update("update guarantee_access_record set access_status=?, update_time=now() "
                + "where id=? and tenant_id=? and access_status='PENDING' and is_deleted=0",
                status, id, TenantContext.require());
        if (updated == 0) {
            throw BizException.notFound("访客记录不存在或已处理");
        }
        return Map.of("id", id, "accessStatus", status);
    }

    public record CreateCmd(Long projectId, Long houseId, Long personId, String visitorName,
                            String visitorPhone, String purpose, LocalDateTime validStart,
                            LocalDateTime validEnd) {
    }
}
