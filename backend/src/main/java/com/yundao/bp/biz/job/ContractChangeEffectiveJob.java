package com.yundao.bp.biz.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizContractChange;
import com.yundao.bp.biz.mapper.BizContractChangeMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import java.time.LocalDate;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/** 合同变更到期生效。 */
@Component
public class ContractChangeEffectiveJob {

    private static final Logger log = LoggerFactory.getLogger(ContractChangeEffectiveJob.class);

    private final BizContractChangeMapper changeMapper;
    private final BizContractMapper contractMapper;
    private final com.fasterxml.jackson.databind.ObjectMapper json =
            new com.fasterxml.jackson.databind.ObjectMapper();

    public ContractChangeEffectiveJob(BizContractChangeMapper changeMapper,
                                      BizContractMapper contractMapper) {
        this.changeMapper = changeMapper;
        this.contractMapper = contractMapper;
    }

    @Scheduled(cron = "0 20 1 * * ?")
    public void applyDue() {
        try {
            java.util.List<BizContractChange> list = changeMapper.selectList(
                    new LambdaQueryWrapper<BizContractChange>()
                            .eq(BizContractChange::getApproveStatus, "APPROVED")
                            .and(w -> w.isNull(BizContractChange::getApplied)
                                    .or().eq(BizContractChange::getApplied, 0))
                            .le(BizContractChange::getEffectiveDate, LocalDate.now()));
            for (BizContractChange e : list) {
                try {
                    BizContract ct = contractMapper.selectById(e.getContractId());
                    if (ct == null) continue;
                    Map<String, Object> after = json.readValue(
                            e.getAfterJson() == null ? "{}" : e.getAfterJson(), Map.class);
                    if (after.containsKey("monthlyRent")) {
                        ct.setMonthlyRent(new java.math.BigDecimal(
                                String.valueOf(after.get("monthlyRent"))));
                    }
                    if (after.containsKey("leaseEnd")) {
                        ct.setLeaseEnd(LocalDate.parse(String.valueOf(after.get("leaseEnd"))));
                    }
                    ct.setUpdateTime(java.time.LocalDateTime.now());
                    contractMapper.updateById(ct);
                    e.setApplied(1);
                    e.setUpdateTime(java.time.LocalDateTime.now());
                    changeMapper.updateById(e);
                    log.info("合同变更 {} 已到期生效", e.getId());
                } catch (Exception ex) {
                    log.warn("合同变更 {} 生效失败：{}", e.getId(), ex.getMessage());
                }
            }
        } catch (Exception e) {
            log.warn("合同变更生效任务异常：{}", e.getMessage());
        }
    }
}
