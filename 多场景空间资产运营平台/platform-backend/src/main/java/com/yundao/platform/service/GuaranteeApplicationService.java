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
import org.springframework.transaction.annotation.Transactional;

@Service
public class GuaranteeApplicationService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;

    public GuaranteeApplicationService(JdbcTemplate jdbc, IdGenerator idGen) {
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    public List<Map<String, Object>> list(long projectId) {
        return jdbc.queryForList(
                "select a.id, a.application_no applicationNo, a.project_id projectId, "
                        + "a.applicant_person_id applicantPersonId, p.person_name applicantName, "
                        + "a.application_type applicationType, a.family_size familySize, "
                        + "a.contact_phone contactPhone, a.income_level incomeLevel, "
                        + "a.housing_status housingStatus, a.urgency, a.remark, "
                        + "a.guarantee_type guaranteeType, a.family_type familyType, "
                        + "a.subsidy_status subsidyStatus, a.archive_no archiveNo, "
                        + "a.application_status applicationStatus, a.submit_time submitTime, "
                        + "a.review_time reviewTime, a.review_comment reviewComment "
                        + "from guarantee_application a left join bp_person p on p.id=a.applicant_person_id "
                        + "where a.tenant_id=? and a.project_id=? and a.is_deleted=0 order by a.id desc",
                TenantContext.require(), projectId);
    }

    public Map<String, Object> create(ApplicationCmd cmd) {
        String tenant = TenantContext.require();
        requireProject(cmd.projectId());
        if (cmd.applicantPersonId() == null || cmd.applicationNo() == null
                || cmd.applicationNo().isBlank()) {
            throw BizException.param("申请编号和申请人不能为空");
        }
        if (count("select count(*) from bp_person where id=? and tenant_id=? and is_deleted=0",
                cmd.applicantPersonId(), tenant) == 0) {
            throw BizException.param("申请人不存在");
        }
        int familySize = cmd.familySize() == null ? 1 : cmd.familySize();
        if (familySize < 1) {
            throw BizException.param("家庭人数必须大于 0");
        }
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_application(id,tenant_id,project_id,application_no,"
                            + "applicant_person_id,application_type,family_size,contact_phone,income_level,"
                            + "housing_status,urgency,remark,guarantee_type,family_type,subsidy_status,archive_no,"
                            + "application_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'DRAFT',0)",
                    id, tenant, cmd.projectId(), cmd.applicationNo().trim(), cmd.applicantPersonId(),
                    cmd.applicationType() == null ? "PUBLIC_RENTAL" : cmd.applicationType(), familySize,
                    cmd.contactPhone(), cmd.incomeLevel(), cmd.housingStatus(), cmd.urgency(), cmd.remark(),
                    cmd.guaranteeType(), cmd.familyType(), cmd.subsidyStatus(), cmd.archiveNo());
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("申请编号已存在");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("applicationNo", cmd.applicationNo());
        out.put("applicationStatus", "DRAFT");
        return out;
    }

    public Map<String, Object> submit(long applicationId) {
        Application app = load(applicationId);
        if (!"DRAFT".equals(app.status())) {
            throw BizException.conflict("申请不是草稿状态");
        }
        jdbc.update("update guarantee_application set application_status='SUBMITTED', submit_time=now() "
                + "where id=?", applicationId);
        return Map.of("id", applicationId, "applicationStatus", "SUBMITTED");
    }

    public Map<String, Object> approve(long applicationId, String comment) {
        Application app = load(applicationId);
        if (!"SUBMITTED".equals(app.status())) {
            throw BizException.conflict("申请不是待审核状态");
        }
        jdbc.update("update guarantee_application set application_status='APPROVED', review_time=now(), "
                + "review_comment=? where id=?", comment, applicationId);
        return Map.of("id", applicationId, "applicationStatus", "APPROVED");
    }


    public Map<String, Object> reject(long applicationId, String comment) {
        Application app = load(applicationId);
        if (!"SUBMITTED".equals(app.status())) {
            throw BizException.conflict("申请不是待审核状态");
        }
        jdbc.update("update guarantee_application set application_status='REJECTED', review_time=now(), "
                + "review_comment=? where id=?", comment, applicationId);
        return Map.of("id", applicationId, "applicationStatus", "REJECTED");
    }

    public Map<String, Object> returnForSupplement(long applicationId, String comment) {
        Application app = load(applicationId);
        if (!"SUBMITTED".equals(app.status())) {
            throw BizException.conflict("申请不是待审核状态");
        }
        jdbc.update("update guarantee_application set application_status='RETURNED', review_time=now(), "
                + "review_comment=? where id=?", comment, applicationId);
        return Map.of("id", applicationId, "applicationStatus", "RETURNED");
    }

    public Map<String, Object> resubmit(long applicationId) {
        Application app = load(applicationId);
        if (!"RETURNED".equals(app.status())) {
            throw BizException.conflict("只有退回补充的申请可以重新提交");
        }
        jdbc.update("update guarantee_application set application_status='SUBMITTED', submit_time=now() "
                + "where id=?", applicationId);
        return Map.of("id", applicationId, "applicationStatus", "SUBMITTED");
    }

    @org.springframework.transaction.annotation.Transactional
    public Map<String, Object> joinWaitlist(long applicationId) {
        Application app = load(applicationId);
        if (!"APPROVED".equals(app.status())) {
            throw BizException.param("申请未审核通过，不能进入轮候");
        }
        long waiting = count("select count(*) from guarantee_waitlist where tenant_id=? and project_id=? "
                + "and waitlist_status='WAITING'", TenantContext.require(), app.projectId());
        String queueNo = "Q" + (waiting + 1);
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_waitlist(id,tenant_id,project_id,application_id,queue_no,"
                            + "waitlist_status,is_deleted) values(?,?,?,?,?, 'WAITING',0)",
                    id, TenantContext.require(), app.projectId(), applicationId, queueNo);
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("该申请已在轮候队列");
        }
        jdbc.update("update guarantee_application set application_status='WAITLISTED', update_time=now() "
                + "where id=? and tenant_id=?", applicationId, TenantContext.require());
        return Map.of("id", id, "applicationId", applicationId, "queueNo", queueNo,
                "waitlistStatus", "WAITING");
    }

    @Transactional
    public Map<String, Object> allocate(long waitlistId, long houseId) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> waitRows = jdbc.queryForList(
                "select id, project_id projectId, application_id applicationId, waitlist_status waitlistStatus "
                        + "from guarantee_waitlist where id=? and tenant_id=? and is_deleted=0 for update",
                waitlistId, tenant);
        if (waitRows.isEmpty()) {
            throw BizException.notFound("轮候记录不存在");
        }
        Map<String, Object> wait = waitRows.get(0);
        if (!"WAITING".equals(String.valueOf(wait.get("waitlistStatus")))) {
            throw BizException.conflict("轮候记录不是待配租状态");
        }
        long projectId = ((Number) wait.get("projectId")).longValue();
        long applicationId = ((Number) wait.get("applicationId")).longValue();
        Map<String, Object> house = jdbc.queryForMap(
                "select id, house_status houseStatus from bp_house where id=? and tenant_id=? and org_id=? "
                        + "and is_deleted=0 for update", houseId, tenant, projectId);
        if (!"VACANT".equals(String.valueOf(house.get("houseStatus")))) {
            throw BizException.conflict("房屋不是空置状态");
        }
        long allocationId = idGen.nextId();
        String allocationNo = "AL" + System.currentTimeMillis() + allocationId % 1000;
        jdbc.update("insert into guarantee_allocation(id,tenant_id,project_id,application_id,house_id,"
                        + "allocation_no,allocation_status,is_deleted) values(?,?,?,?,?,?, 'ALLOCATED',0)",
                allocationId, tenant, projectId, applicationId, houseId, allocationNo);
        jdbc.update("update bp_house set house_status='ALLOCATED', update_time=now() where id=?", houseId);
        jdbc.update("update guarantee_waitlist set waitlist_status='ALLOCATED' where id=?", waitlistId);
        return Map.of("allocationId", allocationId, "allocationNo", allocationNo,
                "houseId", houseId, "allocationStatus", "ALLOCATED");
    }


    @Transactional
    public Map<String, Object> cancelAllocation(long allocationId, String reason) {
        String tenant = TenantContext.require();
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, project_id projectId, application_id applicationId, house_id houseId, "
                        + "contract_id contractId, allocation_status allocationStatus "
                        + "from guarantee_allocation where id=? and tenant_id=? and is_deleted=0 for update",
                allocationId, tenant);
        if (rows.isEmpty()) {
            throw BizException.notFound("配租记录不存在");
        }
        Map<String, Object> row = rows.get(0);
        if (!"ALLOCATED".equals(String.valueOf(row.get("allocationStatus")))) {
            throw BizException.conflict("配租记录不是已配租状态");
        }
        if (row.get("contractId") != null) {
            throw BizException.conflict("已签约的配租不能取消");
        }
        long projectId = ((Number) row.get("projectId")).longValue();
        long applicationId = ((Number) row.get("applicationId")).longValue();
        long houseId = ((Number) row.get("houseId")).longValue();
        jdbc.update("update guarantee_allocation set allocation_status='CANCELLED' where id=?", allocationId);
        jdbc.update("update bp_house set house_status='VACANT', update_time=now() where id=? and tenant_id=?",
                houseId, tenant);
        jdbc.update("update guarantee_waitlist set waitlist_status='WAITING' "
                        + "where tenant_id=? and project_id=? and application_id=? and is_deleted=0",
                tenant, projectId, applicationId);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("allocationId", allocationId);
        out.put("allocationStatus", "CANCELLED");
        out.put("houseId", houseId);
        out.put("waitlistStatus", "WAITING");
        out.put("reason", reason);
        return out;
    }


    public Map<String, Object> discard(long applicationId) {
        Application app = load(applicationId);
        if (!"DRAFT".equals(app.status())) {
            throw BizException.conflict("只有草稿可以作废");
        }
        jdbc.update("update guarantee_application set application_status='DISCARDED', update_time=now() "
                + "where id=? and tenant_id=?", applicationId, TenantContext.require());
        return Map.of("id", applicationId, "applicationStatus", "DISCARDED");
    }

    public Map<String, Object> close(long applicationId) {
        Application app = load(applicationId);
        if (!"CONTRACTED".equals(app.status()) && !"REJECTED".equals(app.status())) {
            throw BizException.conflict("当前状态不能关闭");
        }
        jdbc.update("update guarantee_application set application_status='CLOSED', update_time=now() "
                + "where id=? and tenant_id=?", applicationId, TenantContext.require());
        return Map.of("id", applicationId, "applicationStatus", "CLOSED");
    }

    public List<Map<String, Object>> listWaitlist(long projectId) {
        return jdbc.queryForList(
                "select w.id, w.project_id projectId, w.application_id applicationId, "
                        + "a.application_no applicationNo, p.person_name applicantName, w.queue_no queueNo, "
                        + "w.waitlist_status waitlistStatus, w.joined_time joinedTime "
                        + "from guarantee_waitlist w join guarantee_application a on a.id=w.application_id "
                        + "left join bp_person p on p.id=a.applicant_person_id "
                        + "where w.tenant_id=? and w.project_id=? and w.is_deleted=0 order by w.id",
                TenantContext.require(), projectId);
    }

    public List<Map<String, Object>> allocations(long projectId) {
        return jdbc.queryForList(
                "select al.id, al.allocation_no allocationNo, al.project_id projectId, "
                        + "al.application_id applicationId, a.application_no applicationNo, "
                        + "al.house_id houseId, h.house_name houseName, al.allocation_status allocationStatus, "
                        + "al.allocated_time allocatedTime "
                        + "from guarantee_allocation al join guarantee_application a on a.id=al.application_id "
                        + "left join bp_house h on h.id=al.house_id "
                        + "where al.tenant_id=? and al.project_id=? and al.is_deleted=0 order by al.id desc",
                TenantContext.require(), projectId);
    }

    private Application load(long applicationId) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id, project_id projectId, application_status applicationStatus "
                        + "from guarantee_application where id=? and tenant_id=? and is_deleted=0",
                applicationId, TenantContext.require());
        if (rows.isEmpty()) {
            throw BizException.notFound("保障房申请不存在");
        }
        Map<String, Object> row = rows.get(0);
        return new Application(applicationId, ((Number) row.get("projectId")).longValue(),
                String.valueOf(row.get("applicationStatus")));
    }

    private void requireProject(long projectId) {
        if (count("select count(*) from bp_org where id=? and tenant_id=? and scene_code='GUARANTEE' "
                + "and is_deleted=0", projectId, TenantContext.require()) == 0) {
            throw BizException.param("项目不是保障房项目");
        }
    }

    private long count(String sql, Object... args) {
        Long value = jdbc.queryForObject(sql, Long.class, args);
        return value == null ? 0 : value;
    }

    private record Application(long id, long projectId, String status) {
    }

    public record ApplicationCmd(long projectId, String applicationNo, Long applicantPersonId,
                                 String applicationType, Integer familySize, String contactPhone,
                                 String incomeLevel, String housingStatus, String urgency, String remark,
                                 String guaranteeType, String familyType, String subsidyStatus, String archiveNo) {
    }
}
