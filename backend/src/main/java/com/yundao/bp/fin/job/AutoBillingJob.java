package com.yundao.bp.fin.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.fin.dto.GenerateBillsCmd;
import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.mapper.FinFeeItemMapper;
import com.yundao.bp.fin.service.BillGenerationService;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import com.yundao.bp.sys.service.ConfigService;
import java.time.LocalDate;
import java.time.YearMonth;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 自动出账。
 *
 * <p>主开关：{@code bp.fin.auto-billing.enabled=false}，默认关闭。
 *
 * <p>收费项目按类型选择费用所属期：
 * <ul>
 *   <li>RENT：当月出账，生成日由 {@code billing.rent.generateDay} 配置</li>
 *   <li>PROPERTY / PARKING / OTHER：次月出账，生成上月，生成日由
 *       {@code billing.property.generateDay} 配置</li>
 *   <li>METER / ENERGY / DEPOSIT / LATE_FEE：不自动生成</li>
 * </ul>
 *
 * <p>每日运行，按「租户 + 收费项目 + 费用所属期」写执行标记；失败不写标记，可次日重试。
 */
@Component
public class AutoBillingJob {

    private static final Logger log = LoggerFactory.getLogger(AutoBillingJob.class);

    private final BillGenerationService generationService;
    private final FinFeeItemMapper feeItemMapper;
    private final IamTenantMapper tenantMapper;
    private final ConfigService configService;
    private final boolean enabled;

    public AutoBillingJob(BillGenerationService generationService,
                          FinFeeItemMapper feeItemMapper,
                          IamTenantMapper tenantMapper,
                          ConfigService configService,
                          @Value("${bp.fin.auto-billing.enabled:false}") boolean enabled) {
        this.generationService = generationService;
        this.feeItemMapper = feeItemMapper;
        this.tenantMapper = tenantMapper;
        this.configService = configService;
        this.enabled = enabled;
        if (enabled) {
            log.info("自动出账已启用");
        }
    }

    /** 每日 00:10 运行；到期日/生成日由配置决定。 */
    @Scheduled(cron = "${bp.fin.auto-billing.cron:0 10 0 * * *}")
    public void runDaily() {
        if (!enabled && !configService.getBool("billing.auto.enabled", false)) {
            return;
        }
        runNow();
    }

    /** 手工触发/补跑入口，返回实际执行的项目数。 */
    public int runNow() {
        return runNow(null, null, false);
    }

    /**
     * 手工触发/补跑。
     *
     * @param tenantCode 仅执行指定租户，为空=全部启用租户
     * @param feeItemId  仅执行指定收费项目，为空=全部
     * @param dryRun     true=只试算不落库、不写执行标记
     */
    public int runNow(String tenantCode, Long feeItemId, boolean dryRun) {
        LocalDate today = LocalDate.now();
        int executed = 0;
        for (IamTenant tenant : tenantMapper.selectList(
                new LambdaQueryWrapper<IamTenant>()
                        .eq(IamTenant::getStatus, "ENABLED")
                        .eq(IamTenant::getDeleted, 0))) {
            if (tenant.getTenantCode() == null || tenant.getTenantCode().isBlank()) {
                continue;
            }
            if (tenantCode != null && !tenantCode.isBlank()
                    && !tenantCode.equals(tenant.getTenantCode())) {
                continue;
            }
            TenantContext.set(TenantInfo.of(tenant.getTenantCode()));
            try {
                executed += runTenant(today, feeItemId, dryRun);
            } catch (Exception ex) {
                log.error("自动出账租户 {} 失败：{}", tenant.getTenantCode(), ex.getMessage(), ex);
            } finally {
                TenantContext.clear();
            }
        }
        return executed;
    }

    private int runTenant(LocalDate today, Long feeItemId, boolean dryRun) {
        int executed = 0;
        for (FinFeeItem item : feeItemMapper.selectList(
                new LambdaQueryWrapper<FinFeeItem>()
                        .eq(FinFeeItem::getStatus, "ENABLED")
                        .eq(FinFeeItem::getIsDeleted, 0))) {
            if (feeItemId != null && !feeItemId.equals(item.getId())) {
                continue;
            }
            String mode = billingMode(item);
            if (mode == null) {
                continue;
            }
            int generateDay = configService.getInt(
                    "billing." + ("CURRENT".equals(mode) ? "rent" : "property") + ".generateDay", 1);
            if (today.getDayOfMonth() < Math.min(generateDay, today.lengthOfMonth())) {
                continue;
            }
            YearMonth target = "CURRENT".equals(mode)
                    ? YearMonth.from(today) : YearMonth.from(today).minusMonths(1);
            String period = target.toString();
            String markerKey = "billing.auto.lastRun." + TenantContext.tenantId()
                    + "." + item.getId() + "." + period;
            if (!dryRun && period.equals(configService.getString(markerKey, ""))) {
                continue;
            }
            LocalDate ps = target.atDay(1);
            LocalDate pe = target.atEndOfMonth();
            int creditDays = configService.getInt(
                    "billing." + ("CURRENT".equals(mode) ? "rent" : "property") + ".creditDays",
                    "CURRENT".equals(mode) ? 0 : 30);
            int minPaymentDays = configService.getInt("billing.minPaymentDays", 7);
            LocalDate due = pe.plusDays(creditDays);
            LocalDate minDue = today.plusDays(minPaymentDays);
            if (due.isBefore(minDue)) {
                due = minDue;
            }
            try {
                generationService.generate(new GenerateBillsCmd(
                        item.getId(), null, null, ps, pe, period, due,
                        null, null, null, null, dryRun));
                if (!dryRun) {
                    configService.set(markerKey, period, "auto billing marker");
                }
                executed++;
                log.info("Auto billing {}: tenant {} item {} period {} due {}",
                        dryRun ? "dry-run" : "done", TenantContext.tenantId(),
                        item.getItemName(), period, due);
            } catch (Exception ex) {
                log.error("自动出账失败：租户 {} 项目 {} 期间 {}：{}",
                        TenantContext.tenantId(), item.getItemName(), period, ex.getMessage());
            }
        }
        return executed;
    }

    private static String billingMode(FinFeeItem item) {
        if (item.getCalcMode() == null || "METER".equals(item.getCalcMode())) {
            return null;
        }
        if ("RENT".equals(item.getItemType())) {
            return "CURRENT";
        }
        if ("PROPERTY".equals(item.getItemType()) || "PARKING".equals(item.getItemType())
                || "OTHER".equals(item.getItemType())) {
            return "PREVIOUS";
        }
        return null;
    }
}
