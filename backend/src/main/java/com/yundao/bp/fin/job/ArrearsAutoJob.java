package com.yundao.bp.fin.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.fin.dto.ArrearsActionCreateCmd;
import com.yundao.bp.fin.service.ArrearsActionService;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import com.yundao.bp.sys.service.ConfigService;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/** 欠费自动处置：逾期自动冻结、缴清自动解冻恢复。 */
@Component
public class ArrearsAutoJob {

    private static final Logger log = LoggerFactory.getLogger(ArrearsAutoJob.class);

    private final ArrearsActionService actionService;
    private final ConfigService configService;
    private final IamTenantMapper tenantMapper;
    private final JdbcTemplate jdbc;

    public ArrearsAutoJob(ArrearsActionService actionService, ConfigService configService,
                          IamTenantMapper tenantMapper, JdbcTemplate jdbc) {
        this.actionService = actionService;
        this.configService = configService;
        this.tenantMapper = tenantMapper;
        this.jdbc = jdbc;
    }

    @Scheduled(cron = "${bp.arrears.auto.cron:0 30 2 * * *}")
    public void runDaily() {
        runAll();
    }

    public Map<String, Object> runAll() {
        boolean freezeEnabled = configService.getBool("arrears.autoFreezeEnabled", false);
        boolean restoreEnabled = configService.getBool("arrears.autoRestoreEnabled", true);
        int days = Math.max(1, configService.getInt("arrears.autoFreezeDays", 30));
        int created = 0;
        int executed = 0;
        int restored = 0;
        int tenants = 0;
        for (IamTenant t : tenantMapper.selectList(new LambdaQueryWrapper<IamTenant>()
                .eq(IamTenant::getStatus, "ENABLED").eq(IamTenant::getDeleted, 0))) {
            if (t.getTenantCode() == null || t.getTenantCode().isBlank()) {
                continue;
            }
            TenantContext.set(TenantInfo.of(t.getTenantCode()));
            try {
                tenants++;
                if (freezeEnabled) {
                    for (ArrearsActionService.ArrearsSuggestion s : actionService.scanArrears(days)) {
                        if (!s.freezeRecommended() || hasOpenFreeze(s.contractId())) {
                            continue;
                        }
                        var action = actionService.create(new ArrearsActionCreateCmd(
                                s.contractId(), s.personId(), s.arrearsAmount(), s.overdueDays(),
                                s.orgId(), "FREEZE", "EXCLUDE_MAIN_DOOR", false, "AUTO"));
                        created++;
                        actionService.execute(action.id());
                        executed++;
                    }
                }
                if (restoreEnabled) {
                    List<Long> ids = jdbc.queryForList(
                            "select a.id from bp_fin_arrears_action a "
                                    + "where a.action_type = 'FREEZE' and a.action_status = 'EXECUTED' "
                                    + "and not exists (select 1 from bp_fin_bill b "
                                    + " where b.contract_id = a.contract_id and b.is_deleted = 0 "
                                    + " and b.bill_status in ('UNPAID','PARTIAL','OVERDUE') "
                                    + " and b.due_date < curdate())", Long.class);
                    for (Long id : ids) {
                        try {
                            actionService.revoke(id, "auto restore after paid");
                            restored++;
                        } catch (Exception ex) {
                            log.warn("auto restore action {} failed: {}", id, ex.getMessage());
                        }
                    }
                }
            } catch (Exception ex) {
                log.warn("arrears auto job tenant={} failed: {}", t.getTenantCode(), ex.getMessage());
            } finally {
                TenantContext.clear();
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("tenants", tenants);
        out.put("freezeEnabled", freezeEnabled);
        out.put("created", created);
        out.put("executed", executed);
        out.put("restored", restored);
        return out;
    }

    private boolean hasOpenFreeze(Long contractId) {
        Long n = jdbc.queryForObject(
                "select count(*) from bp_fin_arrears_action where contract_id = ? "
                        + "and action_type = 'FREEZE' and action_status in ('PENDING','EXECUTED')",
                Long.class, contractId);
        return n != null && n > 0;
    }
}
