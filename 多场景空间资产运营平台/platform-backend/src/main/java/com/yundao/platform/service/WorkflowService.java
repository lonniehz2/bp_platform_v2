package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class WorkflowService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public WorkflowService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    @Transactional
    public Map<String, Object> createFlow(FlowCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.sceneCode() == null || cmd.bizType() == null || cmd.flowName() == null
                || cmd.flowName().isBlank() || cmd.nodes() == null || cmd.nodes().isEmpty()) {
            throw BizException.param("场景、业务类型、流程名称、节点不能为空");
        }
        long flowId = idGen.nextId();
        try {
            jdbc.update("insert into bp_wf_flow(id,tenant_id,scene_code,biz_type,flow_name,flow_status,is_deleted) "
                            + "values(?,?,?,?,?,'ENABLED',0)",
                    flowId, tenant, cmd.sceneCode(), cmd.bizType(), cmd.flowName().trim());
            int seq = 1;
            for (NodeCmd node : cmd.nodes()) {
                if (node.nodeName() == null || node.nodeName().isBlank()) {
                    throw BizException.param("节点名称不能为空");
                }
                jdbc.update("insert into bp_wf_node(id,tenant_id,flow_id,node_seq,node_name,approver_role,node_status) "
                                + "values(?,?,?,?,?,?,'ENABLED')",
                        idGen.nextId(), tenant, flowId, seq++, node.nodeName().trim(), node.approverRole());
            }
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("审批流程已存在");
        }
        return Map.of("id", flowId, "flowName", cmd.flowName());
    }

    public List<Map<String, Object>> flows(String sceneCode, String bizType) {
        return jdbc.queryForList(
                "select f.id, f.scene_code sceneCode, f.biz_type bizType, f.flow_name flowName, "
                        + "f.flow_status flowStatus, count(n.id) nodeCount "
                        + "from bp_wf_flow f left join bp_wf_node n on n.flow_id=f.id "
                        + "where f.tenant_id=? and f.is_deleted=0 "
                        + "and (? is null or f.scene_code=?) and (? is null or f.biz_type=?) "
                        + "group by f.id, f.scene_code, f.biz_type, f.flow_name, f.flow_status order by f.id desc",
                TenantContext.require(), sceneCode, sceneCode, bizType, bizType);
    }

    public long findFlowId(String sceneCode, String bizType) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id from bp_wf_flow where tenant_id=? and scene_code=? and biz_type=? "
                        + "and flow_status='ENABLED' and is_deleted=0 order by id desc limit 1",
                TenantContext.require(), sceneCode, bizType);
        if (rows.isEmpty()) {
            throw BizException.param("未配置审批流程");
        }
        return ((Number) rows.get(0).get("id")).longValue();
    }

    public Map<String, Object> submit(long flowId, SubmitCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.bizId() == null || cmd.bizType() == null) {
            throw BizException.param("业务类型和业务 ID 不能为空");
        }
        List<Map<String, Object>> nodes = jdbc.queryForList(
                "select id, node_seq nodeSeq, node_name nodeName from bp_wf_node "
                        + "where tenant_id=? and flow_id=? and node_status='ENABLED' order by node_seq",
                tenant, flowId);
        if (nodes.isEmpty()) {
            throw BizException.param("审批流程没有可用节点");
        }
        long taskId = idGen.nextId();
        try {
            jdbc.update("insert into bp_wf_task(id,tenant_id,project_id,biz_type,biz_id,flow_id,"
                            + "current_node_id,task_status,submitter_name,amount,summary,is_deleted) "
                            + "values(?,?,?,?,?,?,?, 'APPROVING',?,?,?,0)",
                    taskId, tenant, cmd.projectId(), cmd.bizType(), cmd.bizId(), flowId,
                    nodes.get(0).get("id"), cmd.submitterName(), cmd.amount(), cmd.summary());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("该业务已提交审批");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("taskId", taskId);
        out.put("currentNode", nodes.get(0).get("nodeName"));
        out.put("taskStatus", "APPROVING");
        return out;
    }

    @Transactional
    public Map<String, Object> approve(long taskId, ActionCmd cmd) {
        return action(taskId, cmd, "APPROVE");
    }

    @Transactional
    public Map<String, Object> reject(long taskId, ActionCmd cmd) {
        return action(taskId, cmd, "REJECT");
    }

    private Map<String, Object> action(long taskId, ActionCmd cmd, String action) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, flow_id flowId, current_node_id currentNodeId, task_status taskStatus "
                        + "from bp_wf_task where id=? and tenant_id=? and is_deleted=0 for update",
                taskId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("审批任务不存在");
        }
        Map<String, Object> task = rows.get(0);
        if (!"APPROVING".equals(String.valueOf(task.get("taskStatus")))) {
            throw BizException.conflict("审批任务已结束");
        }
        long nodeId = ((Number) task.get("currentNodeId")).longValue();
        jdbc.update("insert into bp_wf_record(id,tenant_id,task_id,node_id,approver_name,action,comment_text) "
                        + "values(?,?,?,?,?,?,?)",
                idGen.nextId(), tenant, taskId, nodeId, cmd.approverName(), action, cmd.comment());
        if ("REJECT".equals(action)) {
            jdbc.update("update bp_wf_task set task_status='REJECTED', finish_time=now() where id=?", taskId);
            return Map.of("taskId", taskId, "taskStatus", "REJECTED");
        }
        Map<String, Object> next = jdbc.queryForList(
                "select n.id, n.node_name nodeName from bp_wf_node n "
                        + "join bp_wf_node c on c.flow_id=n.flow_id and c.id=? "
                        + "where n.node_seq > c.node_seq and n.node_status='ENABLED' "
                        + "order by n.node_seq limit 1", nodeId).stream().findFirst().orElse(null);
        if (next == null) {
            jdbc.update("update bp_wf_task set task_status='APPROVED', finish_time=now() where id=?", taskId);
            return Map.of("taskId", taskId, "taskStatus", "APPROVED");
        }
        jdbc.update("update bp_wf_task set current_node_id=? where id=?", next.get("id"), taskId);
        return Map.of("taskId", taskId, "taskStatus", "APPROVING", "currentNode", next.get("nodeName"));
    }

    public List<Map<String, Object>> tasks(String status) {
        return jdbc.queryForList(
                "select t.id, t.project_id projectId, t.biz_type bizType, t.biz_id bizId, "
                        + "t.task_status taskStatus, t.submitter_name submitterName, t.amount, t.summary, "
                        + "n.node_name currentNode, t.submit_time submitTime, t.finish_time finishTime "
                        + "from bp_wf_task t left join bp_wf_node n on n.id=t.current_node_id "
                        + "where t.tenant_id=? and t.is_deleted=0 and (? is null or t.task_status=?) "
                        + "order by t.id desc",
                TenantContext.require(), status, status);
    }

    public List<Map<String, Object>> records(long taskId) {
        return jdbc.queryForList(
                "select r.id, r.node_id nodeId, n.node_name nodeName, r.approver_name approverName, "
                        + "r.action, r.comment_text comment, r.action_time actionTime "
                        + "from bp_wf_record r left join bp_wf_node n on n.id=r.node_id "
                        + "where r.tenant_id=? and r.task_id=? order by r.id",
                TenantContext.require(), taskId);
    }

    public record FlowCmd(String sceneCode, String bizType, String flowName, List<NodeCmd> nodes) {
    }

    public record NodeCmd(String nodeName, String approverRole) {
    }

    public record SubmitCmd(Long projectId, String bizType, Long bizId, String submitterName,
                            BigDecimal amount, String summary) {
    }

    public record ActionCmd(String approverName, String comment) {
    }
}
