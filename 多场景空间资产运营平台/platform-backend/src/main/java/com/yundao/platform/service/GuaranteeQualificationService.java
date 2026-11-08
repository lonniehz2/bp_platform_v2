package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.id.IdGenerator;
import com.yundao.platform.common.tenant.TenantContext;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class GuaranteeQualificationService {

    private final JdbcTemplate jdbc;
    private final IdGenerator idGen;
    private final GuaranteeContractService contractService;

    public GuaranteeQualificationService(JdbcTemplate jdbc, IdGenerator idGen,
                                         GuaranteeContractService contractService) {
        this.jdbc = jdbc;
        this.idGen = idGen;
        this.contractService = contractService;
    }

    public List<Map<String, Object>> list(long contractId) {
        contractService.load(contractId);
        return jdbc.queryForList(
                "select id, contract_id contractId, person_id personId, review_type reviewType, "
                        + "review_year reviewYear, review_status reviewStatus, review_date reviewDate, "
                        + "reviewer_name reviewerName, review_comment reviewComment, "
                        + "next_review_date nextReviewDate from guarantee_qualification_review "
                        + "where tenant_id=? and contract_id=? and is_deleted=0 order by review_year desc, id desc",
                TenantContext.require(), contractId);
    }

    public Map<String, Object> create(long contractId, ReviewCmd cmd) {
        GuaranteeContractService.Contract contract = contractService.load(contractId);
        if (!"ACTIVE".equals(contract.contractStatus())) {
            throw BizException.param("合同不是生效状态");
        }
        int year = cmd.reviewYear() == null ? LocalDate.now().getYear() : cmd.reviewYear();
        String type = cmd.reviewType() == null ? "ANNUAL" : cmd.reviewType();
        long id = idGen.nextId();
        try {
            jdbc.update("insert into guarantee_qualification_review(id,tenant_id,project_id,contract_id,person_id,"
                            + "review_type,review_year,review_status,is_deleted) "
                            + "values(?,?,?,?,?,?,?, 'PENDING',0)",
                    id, TenantContext.require(), contract.projectId(), contractId, contract.personId(), type, year);
        } catch (DataIntegrityViolationException e) {
            throw BizException.conflict("该合同该年度复核已存在");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("id", id);
        out.put("contractId", contractId);
        out.put("reviewType", type);
        out.put("reviewYear", year);
        out.put("reviewStatus", "PENDING");
        return out;
    }

    public Map<String, Object> complete(long reviewId, CompleteCmd cmd) {
        String tenant = TenantContext.require();
        if (cmd.result() == null || !List.of("PASSED", "FAILED").contains(cmd.result())) {
            throw BizException.param("复核结果必须是 PASSED 或 FAILED");
        }
        long updated = jdbc.update("update guarantee_qualification_review set review_status=?, review_date=curdate(), "
                        + "reviewer_name=?, review_comment=?, next_review_date=? "
                        + "where id=? and tenant_id=? and review_status='PENDING' and is_deleted=0",
                cmd.result(), cmd.reviewerName(), cmd.comment(), cmd.nextReviewDate(), reviewId, tenant);
        if (updated == 0) {
            throw BizException.conflict("复核记录不存在或已处理");
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("reviewId", reviewId);
        out.put("reviewStatus", cmd.result());
        return out;
    }

    public record ReviewCmd(String reviewType, Integer reviewYear) {
    }

    public record CompleteCmd(String result, String reviewerName, String comment, LocalDate nextReviewDate) {
    }
}
