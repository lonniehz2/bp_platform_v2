# -*- coding: utf-8 -*-
"""合同变更：批准后按生效日写回（新增 applied 标记 + 定时生效）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return s


# 实体加 applied
p = os.path.join(BE, 'biz', 'entity', 'BizContractChange.java')
s = io.open(p, encoding='utf-8').read()
if 'applied' not in s:
    s = s.replace('''    private LocalDate effectiveDate;''', '''    private LocalDate effectiveDate;

    /** 是否已写回合同（0 未生效，1 已生效） */
    private Integer applied;''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 实体 applied')

# 服务：apply 抽取 + 按生效日
p = os.path.join(BE, 'biz', 'service', 'impl', 'ContractChangeServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'applyToContract' not in s:
    # 替换 approve 中的写回段为调用
    s = s.replace('''        // ⭐ 真正写回合同
        if (after.containsKey("monthlyRent")) {''', '''        // 未到生效日：先记批准，等定时任务到期写回
        java.time.LocalDate eff = e.getEffectiveDate() == null
                ? java.time.LocalDate.now() : e.getEffectiveDate();
        if (eff.isAfter(java.time.LocalDate.now())) {
            e.setApproveStatus(ApproveStatus.APPROVED.name());
            e.setApplied(0);
            e.setUpdateTime(LocalDateTime.now());
            mapper.updateById(e);
            log.info("变更单 {} 已批准，生效日 {}，到期自动写回", id, eff);
            return ChangeVO.from(e);
        }
        applyToContract(ct, after);

        // ⭐ 真正写回合同
        if (false && after.containsKey("monthlyRent")) {''', 1)
    # 在文件末尾前插入 applyToContract（复制原逻辑）
    s = s.replace('''    @Override
    @Transactional(rollbackFor = Exception.class)
    public ChangeVO reject''', '''    /** 把变更内容写回合同（批准且到生效日时调用）。 */
    private void applyToContract(BizContract ct, Map<String, Object> after) {
        if (after.containsKey("monthlyRent")) {
            BigDecimal newRent = new BigDecimal(String.valueOf(after.get("monthlyRent")))
                    .setScale(2, RoundingMode.HALF_UP);
            log.info("合同 {} 租金调整：{} → {}", ct.getContractNo(), ct.getMonthlyRent(), newRent);
            ct.setMonthlyRent(newRent);
            if (ct.getSubsidyAmount() != null) {
                ct.setActualPay(newRent.subtract(ct.getSubsidyAmount())
                        .setScale(2, RoundingMode.HALF_UP));
            }
        }
        if (after.containsKey("leaseEnd")) {
            ct.setLeaseEnd(LocalDate.parse(String.valueOf(after.get("leaseEnd"))));
        }
        if (after.containsKey("lesseePersonId")) {
            ct.setLesseePersonId(Long.valueOf(String.valueOf(after.get("lesseePersonId"))));
            Object nm = after.get("lesseeName");
            if (nm != null) {
                ct.setLesseeName(String.valueOf(nm));
            }
        }
        ct.setUpdateTime(LocalDateTime.now());
        contractMapper.updateById(ct);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ChangeVO reject''', 1)
    # approve 结尾设置 applied=1
    s = s.replace('''        e.setApproveStatus(ApproveStatus.APPROVED.name());
        if (e.getEffectiveDate() == null) {
            e.setEffectiveDate(LocalDate.now());
        }''', '''        e.setApproveStatus(ApproveStatus.APPROVED.name());
        e.setApplied(1);
        if (e.getEffectiveDate() == null) {
            e.setEffectiveDate(LocalDate.now());
        }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 批准/生效拆分')

# 定时任务
p = os.path.join(BE, 'biz', 'job', 'ContractChangeEffectiveJob.java')
if not os.path.exists(p):
    code = '''package com.yundao.bp.biz.job;

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

/** 合同变更到期生效：已批准、未写回、生效日已到 -> 写回合同。 */
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
                    if (ct == null) {
                        continue;
                    }
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
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(code)
    print('  ✔ 生效任务')
