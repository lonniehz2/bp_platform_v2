package com.yundao.platform.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GuaranteeContractChangeService {

    private static final String BIZ_TYPE = "GUARANTEE_CONTRACT_CHANGE";

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final ObjectMapper objectMapper;
    private final GuaranteeContractService contractService;
    private final WorkflowService workflowService;

    public GuaranteeContractChangeService(JdbcTemplate jdbc, IdGenerator idGen,
                                          ObjectMapper objectMapper,
                                          GuaranteeContractService contractService,
                                          WorkflowService workflowService) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.objectMapper = objectMapper;
        this.contractService = contractService;
        this.workflowService = workflowService;
    }

    public List<Map<String, Object>> list(long contractId) {
        contractService.load(contractId);
        return jdbc.queryForList(
                "select id, contract_id contractId, change_type changeType, effective_date effectiveDate, "
                        + "change_status changeStatus, reason, workflow_task_id workflowTaskId, "
                        + "before_json beforeJson, after_json afterJson, create_time createTime "
                        + "from guarantee_contract_change where tenant_id=? and contract_id=? and is_deleted=0 "
                        + "order by id desc",
                TenantContext.require(), contractId);
    }

    public Map<String, Object> create(long contractId, ChangeCmd cmd) {
        GuaranteeContractService.Contract contract = contractService.load(contractId);
        if (!"ACTIVE".equals(contract.contractStatus())) {
            throw BizException.param("合同不是生效状态");
        }
        if (cmd.changeType() == null || cmd.changeType().isBlank() || cmd.after() == null) {
            throw BizException.param("变更类型和变更内容不能为空");
        }
        if (!List.of("RENT_CHANGE", "TERM_CHANGE", "ROOM_CHANGE", "TERMINATION")
                .contains(cmd.changeType())) {
            throw BizException.param("变更类型不合法");
        }
        Map<String, Object> before = new LinkedHashMap<>();
        before.put("contractNo", contract.contractNo());
        before.put("houseId", contract.houseId());
        before.put("personId", contract.personId());
        before.put("rentAmount", contract.rentAmount());
        before.put("endDate", String.valueOf(contract.endDate()));
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_contract_change(id,tenant_id,project_id,contract_id,"
                            + "change_type,before_json,after_json,effective_date,change_status,reason,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?, 'DRAFT',?,0)",
                    id, contract.tenantId(), contract.projectId(), contractId, cmd.changeType(),
                    objectMapper.writeValueAsString(before),
                    objectMapper.writeValueAsString(cmd.after()),
                    cmd.effectiveDate(), cmd.reason());
        } catch (Exception e) {
            throw BizException.param("变更内容 JSON 生成失败");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("contractId", contractId);
        out.put("changeType", cmd.changeType());
        out.put("changeStatus", "DRAFT");
        return out;
    }

    @Transactional
    public Map<String, Object> submit(long changeId) {
        Change change = load(changeId, true);
        if (!"DRAFT".equals(change.changeStatus())) {
            throw BizException.conflict("变更单不是草稿状态");
        }
        long flowId = workflowService.findFlowId("GUARANTEE", BIZ_TYPE);
        Map<String, Object> task = workflowService.submit(flowId,
                new WorkflowService.SubmitCmd(change.projectId(), BIZ_TYPE, changeId,
                        "保障房经办人", BigDecimal.ZERO, "合同变更：" + change.changeType()));
        long taskId = ((Number) task.get("taskId")).longValue();
        jdbc.update("update guarantee_contract_change set change_status='APPROVING', workflow_task_id=? "
                + "where id=?", taskId, changeId);
        return Map.of("changeId", changeId, "taskId", taskId, "changeStatus", "APPROVING");
    }

    @Transactional
    public Map<String, Object> approve(long changeId, WorkflowService.ActionCmd cmd) {
        Change change = load(changeId, true);
        if (!"APPROVING".equals(change.changeStatus())) {
            throw BizException.conflict("变更单不在审批中");
        }
        Map<String, Object> task = workflowService.approve(change.workflowTaskId(), cmd);
        String taskStatus = String.valueOf(task.get("taskStatus"));
        if ("APPROVED".equals(taskStatus)) {
            apply(change);
            jdbc.update("update guarantee_contract_change set change_status='APPROVED' where id=?", changeId);
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("changeId", changeId);
        out.put("changeStatus", "APPROVED".equals(taskStatus) ? "APPROVED" : "APPROVING");
        out.put("taskStatus", taskStatus);
        return out;
    }

    @Transactional
    public Map<String, Object> reject(long changeId, WorkflowService.ActionCmd cmd) {
        Change change = load(changeId, true);
        if (!"APPROVING".equals(change.changeStatus())) {
            throw BizException.conflict("变更单不在审批中");
        }
        workflowService.reject(change.workflowTaskId(), cmd);
        jdbc.update("update guarantee_contract_change set change_status='REJECTED' where id=?", changeId);
        return Map.of("changeId", changeId, "changeStatus", "REJECTED");
    }

    private void apply(Change change) {
        Map<String, Object> after;
        try {
            after = objectMapper.readValue(change.afterJson(), new TypeReference<>() {
            });
        } catch (Exception e) {
            throw BizException.param("变更内容解析失败");
        }
        switch (change.changeType()) {
            case "RENT_CHANGE" -> {
                BigDecimal rent = decimal(after.get("rentAmount"), "租金");
                if (rent.signum() < 0) {
                    throw BizException.param("租金不能为负数");
                }
                jdbc.update("update guarantee_contract set rent_amount=?, update_time=now() where id=?",
                        rent, change.contractId());
            }
            case "TERM_CHANGE" -> {
                LocalDate endDate = date(after.get("endDate"), "结束日期");
                jdbc.update("update guarantee_contract set end_date=?, update_time=now() where id=?",
                        endDate, change.contractId());
            }
            case "ROOM_CHANGE" -> {
                long houseId = ((Number) after.get("houseId")).longValue();
                if (jdbc.queryForObject("select count(*) from bp_house where id=? and tenant_id=? "
                                + "and org_id=? and is_deleted=0", Long.class, houseId,
                        TenantContext.require(), change.projectId()) == 0) {
                    throw BizException.param("新房屋不属于当前项目");
                }
                jdbc.update("update guarantee_contract set house_id=?, update_time=now() where id=?",
                        houseId, change.contractId());
            }
            case "TERMINATION" -> {
                LocalDate endDate = change.effectiveDate() == null
                        ? date(after.get("endDate"), "终止日期") : change.effectiveDate();
                jdbc.update("update guarantee_contract set contract_status='TERMINATED', end_date=?, "
                        + "update_time=now() where id=?", endDate, change.contractId());
            }
            default -> throw BizException.param("不支持的变更类型");
        }
    }

    private BigDecimal decimal(Object value, String name) {
        if (value == null) {
            throw BizException.param(name + "不能为空");
        }
        try {
            return new BigDecimal(String.valueOf(value));
        } catch (Exception e) {
            throw BizException.param(name + "格式不正确");
        }
    }

    private LocalDate date(Object value, String name) {
        if (value == null) {
            throw BizException.param(name + "不能为空");
        }
        try {
            return LocalDate.parse(String.valueOf(value));
        } catch (Exception e) {
            throw BizException.param(name + "格式不正确");
        }
    }

    private Change load(long changeId, boolean forUpdate) {
        String sql = "select id, project_id projectId, contract_id contractId, change_type changeType, "
                + "after_json afterJson, effective_date effectiveDate, change_status changeStatus, "
                + "workflow_task_id workflowTaskId from guarantee_contract_change "
                + "where id=? and tenant_id=? and is_deleted=0" + (forUpdate ? " for update" : "");
        List<Map<String, Object>> rows = jdbc.queryForList(sql, changeId, TenantContext.require());
        if (rows.isEmpty()) {
            throw BizException.notFound("合同变更单不存在");
        }
        Map<String, Object> r = rows.get(0);
        Object task = r.get("workflowTaskId");
        return new Change(changeId, ((Number) r.get("projectId")).longValue(),
                ((Number) r.get("contractId")).longValue(), String.valueOf(r.get("changeType")),
                String.valueOf(r.get("afterJson")),
                r.get("effectiveDate") == null ? null : ((java.sql.Date) r.get("effectiveDate")).toLocalDate(),
                String.valueOf(r.get("changeStatus")), task == null ? null : ((Number) task).longValue());
    }

    private record Change(long id, long projectId, long contractId, String changeType, String afterJson,
                          LocalDate effectiveDate, String changeStatus, Long workflowTaskId) {
    }

    public record ChangeCmd(String changeType, Map<String, Object> after, LocalDate effectiveDate,
                            String reason) {
    }
}
