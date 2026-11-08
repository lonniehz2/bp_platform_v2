package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class WorkOrderService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public WorkOrderService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select w.id, w.order_no orderNo, w.project_id projectId, w.order_type orderType, "
                        + "w.title, w.description, w.house_id houseId, h.house_name houseName, "
                        + "w.person_id personId, p.person_name personName, w.priority, w.order_status orderStatus, "
                        + "w.assignee_name assigneeName, w.create_time createTime, w.finish_time finishTime "
                        + "from guarantee_work_order w left join bp_house h on h.id=w.house_id "
                        + "left join bp_person p on p.id=w.person_id "
                        + "where w.tenant_id=? and w.project_id=? and w.is_deleted=0 order by w.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(CreateCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.projectId() == null || cmd.title() == null || cmd.title().isBlank()) {
            throw BizException.param("项目、标题不能为空");
        }
        String no = cmd.orderNo() == null || cmd.orderNo().isBlank()
                ? "WO" + System.currentTimeMillis() : cmd.orderNo().trim();
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_work_order(id,tenant_id,project_id,order_no,order_type,title,"
                            + "description,house_id,person_id,priority,order_status,assignee_name,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?, 'PENDING',?,0)",
                    id, tenant, cmd.projectId(), no,
                    cmd.orderType() == null ? "REPAIR" : cmd.orderType(),
                    cmd.title().trim(), cmd.description(), cmd.houseId(), cmd.personId(),
                    cmd.priority() == null ? "NORMAL" : cmd.priority(), cmd.assigneeName());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("工单号已存在");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("orderNo", no);
        out.put("orderStatus", "PENDING");
        return out;
    }

    public Map<String, Object> update(long orderId, UpdateCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.orderStatus() != null && !List.of("PENDING", "PROCESSING", "DONE", "CLOSED")
                .contains(cmd.orderStatus())) {
            throw BizException.param("工单状态不合法");
        }
        long updated = jdbc.update(
                "update guarantee_work_order set order_status=coalesce(?,order_status), "
                        + "assignee_name=coalesce(?,assignee_name), "
                        + "finish_time=case when ?='DONE' then now() else finish_time end, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                cmd.orderStatus(), cmd.assigneeName(), cmd.orderStatus(), orderId, tenant);
        if (updated == 0) {
            throw BizException.notFound("工单不存在");
        }
        return Map.of("id", orderId, "orderStatus", cmd.orderStatus() == null ? "UNCHANGED" : cmd.orderStatus());
    }

    public record CreateCmd(Long projectId, String orderNo, String orderType, String title,
                            String description, Long houseId, Long personId, String priority,
                            String assigneeName) {
    }

    public record UpdateCmd(String orderStatus, String assigneeName) {
    }
}
