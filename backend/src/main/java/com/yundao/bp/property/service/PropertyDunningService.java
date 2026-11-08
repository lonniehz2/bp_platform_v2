package com.yundao.bp.property.service;

import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.msg.dto.MessageSendCmd;
import com.yundao.bp.msg.dto.MessageVO;
import com.yundao.bp.msg.service.MessageService;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 物业欠费催缴。第一版采用站内任务记录，短信/微信渠道由外部通道异步发送。 */
@Service
public class PropertyDunningService {

    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;
    private final MessageService messageService;

    public PropertyDunningService(JdbcTemplate jdbc, SnowflakeIdGenerator idGen,
                                  MessageService messageService) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.messageService = messageService;
    }

    public List<Map<String, Object>> arrears(Long projectId, String keyword) {
        requireProject(projectId);
        StringBuilder sql = new StringBuilder(
                "select b.id billId, b.bill_no billNo, b.payer_name payerName, b.house_id houseId, "
                        + "b.period_start periodStart, b.period_end periodEnd, b.payable_amount payableAmount, "
                        + "b.paid_amount paidAmount, b.bill_status billStatus, b.due_date dueDate, "
                        + "h.house_name houseName, p.phone phone "
                        + "from prop_bill b left join bp_asset_house h on h.id=b.house_id "
                        + "left join prop_owner_unit ou on ou.house_id=b.house_id and ou.is_primary=1 "
                        + "and ou.status='ACTIVE' and ou.is_deleted=0 "
                        + "left join bp_person p on p.id=ou.person_id "
                        + "where b.tenant_id=? and b.project_id=? and b.is_deleted=0 "
                        + "and b.bill_status in ('PENDING','OVERDUE','PARTIAL')");
        java.util.List<Object> args = new java.util.ArrayList<>(
                List.of(TenantContext.tenantId(), projectId));
        if (keyword != null && !keyword.isBlank()) {
            sql.append(" and (b.bill_no like ? or b.payer_name like ? or h.house_name like ?)");
            String k = "%" + keyword.trim() + "%";
            args.add(k); args.add(k); args.add(k);
        }
        sql.append(" order by b.due_date asc, b.id desc limit 500");
        return jdbc.queryForList(sql.toString(), args.toArray());
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> send(Long projectId, SendCmd cmd) {
        requireProject(projectId);
        if (cmd.billIds() == null || cmd.billIds().isEmpty()) {
            throw BizException.paramInvalid("请选择欠费账单");
        }
        String channels = cmd.channels() == null || cmd.channels().isBlank()
                ? "SMS" : cmd.channels();
        long taskId = idGen.nextId();
        String taskNo = "DUN" + taskId;
        jdbc.update("insert into prop_dunning_task(id,tenant_id,project_id,task_no,channels,reason,"
                        + "task_status,total_count,success_count,fail_count,create_by,create_time) "
                        + "values(?,?,?,?,?,?, 'SENT',?,0,0,?,now())",
                taskId, TenantContext.tenantId(), projectId, taskNo, channels, cmd.reason(),
                cmd.billIds().size(), String.valueOf(TenantContext.userId()));
        int success = 0, fail = 0;
        for (Long billId : cmd.billIds()) {
            List<Map<String, Object>> bills = jdbc.queryForList(
                    "select b.id, b.bill_no billNo, b.payer_name payerName, b.payable_amount payableAmount, "
                            + "b.paid_amount paidAmount, h.house_name houseName, p.phone phone "
                            + "from prop_bill b left join bp_asset_house h on h.id=b.house_id "
                            + "left join prop_owner_unit ou on ou.house_id=b.house_id and ou.is_primary=1 "
                            + "and ou.status='ACTIVE' and ou.is_deleted=0 "
                            + "left join bp_person p on p.id=ou.person_id "
                            + "where b.id=? and b.tenant_id=? and b.project_id=?",
                    billId, TenantContext.tenantId(), projectId);
            if (bills.isEmpty()) {
                fail++;
                continue;
            }
            Map<String, Object> b = bills.get(0);
            BigDecimal due = ((BigDecimal) b.get("payableAmount"))
                    .subtract((BigDecimal) b.get("paidAmount"));
            String content = "尊敬的业主，您有 " + due + " 元费用待缴，房号 "
                    + b.get("houseName") + "，请尽快缴纳。";
            boolean anySuccess = false;
            for (String channel : channels.split(",")) {
                String ch = channel.trim();
                if (ch.isEmpty()) continue;
                MessageVO vo = null;
                try {
                    vo = messageService.send(new MessageSendCmd(null, "PROPERTY_DUNNING",
                            billId, ch, "PERSON", String.valueOf(b.get("payerName")),
                            String.valueOf(b.get("payerName")),
                            b.get("phone") == null ? "SIM" : String.valueOf(b.get("phone")),
                            "物业费催缴", content, null));
                } catch (Exception e) {
                    jdbc.update("insert into prop_dunning_record(id,tenant_id,task_id,bill_id,payer_name,"
                                    + "house_name,amount,channel,recipient,content,send_status,error_msg,create_time) "
                                    + "values(?,?,?,?,?,?,?,?,?,?, 'FAILED',?,now())",
                            idGen.nextId(), TenantContext.tenantId(), taskId, billId,
                            b.get("payerName"), b.get("houseName"), due, ch,
                            b.get("phone"), content, e.getMessage());
                    continue;
                }
                String status = vo == null ? "FAILED" : vo.sendStatus();
                if ("SUCCESS".equals(status)) anySuccess = true;
                jdbc.update("insert into prop_dunning_record(id,tenant_id,task_id,bill_id,payer_name,"
                                + "house_name,amount,channel,recipient,content,send_status,error_msg,"
                                + "send_time,create_time) values(?,?,?,?,?,?,?,?,?,?,?,?,now(),now())",
                        idGen.nextId(), TenantContext.tenantId(), taskId, billId,
                        b.get("payerName"), b.get("houseName"), due, ch,
                        vo == null ? null : vo.receiverAddr(), content, status,
                        vo == null ? null : vo.failReason());
            }
            if (anySuccess) success++; else fail++;
        }
        jdbc.update("update prop_dunning_task set success_count=?, fail_count=? where id=?",
                success, fail, taskId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("taskId", taskId);
        out.put("taskNo", taskNo);
        out.put("total", cmd.billIds().size());
        out.put("success", success);
        out.put("fail", fail);
        return out;
    }

    public List<Map<String, Object>> tasks(Long projectId) {
        requireProject(projectId);
        return jdbc.queryForList(
                "select id, task_no taskNo, channels, reason, task_status taskStatus, "
                        + "total_count totalCount, success_count successCount, fail_count failCount, "
                        + "create_time createTime from prop_dunning_task "
                        + "where tenant_id=? and project_id=? order by id desc limit 100",
                TenantContext.tenantId(), projectId);
    }

    public List<Map<String, Object>> records(Long taskId) {
        return jdbc.queryForList(
                "select id, bill_id billId, payer_name payerName, house_name houseName, amount, "
                        + "channel, recipient, content, send_status sendStatus, send_time sendTime "
                        + "from prop_dunning_record where tenant_id=? and task_id=? order by id desc",
                TenantContext.tenantId(), taskId);
    }

    private void requireProject(Long projectId) {
        if (projectId == null) throw BizException.paramInvalid("请选择项目");
        Long n = jdbc.queryForObject("select count(*) from prop_project_config "
                        + "where tenant_id=? and org_id=? and is_deleted=0",
                Long.class, TenantContext.tenantId(), projectId);
        if (n == null || n == 0) throw BizException.notFound("物业项目");
    }

    public record SendCmd(List<Long> billIds, String channels, String reason) {
    }
}
