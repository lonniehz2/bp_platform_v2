# -*- coding: utf-8 -*-
"""定时自动出账任务"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
p = os.path.join(BASE, r'fin\job\AutoBillingJob.java')
os.makedirs(os.path.dirname(p), exist_ok=True)

content = '''package com.yundao.bp.fin.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.fin.dto.GenerateBatchCmd;
import com.yundao.bp.fin.dto.GenerateBatchVO;
import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.mapper.FinFeeItemMapper;
import com.yundao.bp.fin.service.BillGenerationService;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 定时自动出账。
 *
 * <p><b>默认关闭</b>：{@code bp.fin.auto-billing.enabled=false}。
 * 生产环境确认计费规则无误后再开启。
 *
 * <p><b>出账周期</b>：默认每月 1 日 02:00（{@code bp.fin.auto-billing.cron}），
 * 出「上一个自然月」的账单。
 *
 * <p><b>参与项目</b>：所有 {@code status=ENABLED} 且
 * {@code calc_mode != METER}（抄表项需逐户录读数）的收费项目。
 *
 * <p><b>幂等</b>：底层按「合同+收费项目+账期」去重，重复触发不会重复出账。
 */
@Component
public class AutoBillingJob {

    private static final Logger log = LoggerFactory.getLogger(AutoBillingJob.class);

    private final BillGenerationService generationService;
    private final FinFeeItemMapper feeItemMapper;
    private final boolean enabled;

    public AutoBillingJob(BillGenerationService generationService,
                          FinFeeItemMapper feeItemMapper,
                          @Value("${bp.fin.auto-billing.enabled:false}") boolean enabled) {
        this.generationService = generationService;
        this.feeItemMapper = feeItemMapper;
        this.enabled = enabled;
        if (enabled) {
            log.info("定时自动出账已启用（每月出上个自然月账单）");
        }
    }

    /** 每月 1 日 02:00 出上一个自然月的账单。 */
    @Scheduled(cron = "${bp.fin.auto-billing.cron:0 0 2 1 * ?}")
    public void runMonthly() {
        if (!enabled) {
            return;
        }
        LocalDate today = LocalDate.now();
        LocalDate lastMonthFirst = today.minusMonths(1).withDayOfMonth(1);
        LocalDate lastMonthLast = today.withDayOfMonth(1).minusDays(1);
        generate(lastMonthFirst, lastMonthLast);
    }

    /**
     * 手动/定时触发出账。
     *
     * @return 汇总结果；未启用或无可出账项目时返回 null
     */
    public GenerateBatchVO generate(LocalDate periodStart, LocalDate periodEnd) {
        List<FinFeeItem> items = feeItemMapper.selectList(new LambdaQueryWrapper<FinFeeItem>()
                .eq(FinFeeItem::getStatus, "ENABLED")
                .ne(FinFeeItem::getCalcMode, "METER"));
        if (items.isEmpty()) {
            log.info("定时出账：没有可参与批量出账的收费项目（METER 类需逐户录读数）");
            return null;
        }
        List<GenerateBatchCmd.Item> list = new ArrayList<>();
        items.forEach(i -> list.add(new GenerateBatchCmd.Item(i.getId(), null)));

        GenerateBatchCmd cmd = new GenerateBatchCmd(list, periodStart, periodEnd,
                periodStart.toString().substring(0, 7), periodStart, null, null, null, null,
                false);
        GenerateBatchVO r = generationService.generateBatch(cmd);
        log.info("定时出账完成：期间 {}~{} 项目 {} 生成 {} 跳过 {} 合计 {}",
                periodStart, periodEnd, items.size(), r.totalGenerated(),
                r.totalSkipped(), r.totalAmount());
        return r;
    }
}
'''

io.open(p, 'w', encoding='utf-8').write(content)
print('  + fin/job/AutoBillingJob.java')
