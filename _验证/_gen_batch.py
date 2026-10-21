# -*- coding: utf-8 -*-
"""批量自动出账增强：多项目批量 + 定时任务"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/dto/GenerateBatchCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.util.List;

/**
 * 多项目批量出账（一次生成租金 + 物业费 + 能耗费等多张账单）。
 *
 * <p>典型用法：每月初对全租户一次性出「租金 + 物业费」。
 * 内部按收费项目逐个调用单项目出账，任一项目失败不影响其它项目。
 *
 * @param items        要出账的收费项目列表
 * @param periodStart  费用起始日
 * @param periodEnd    费用截止日
 * @param billPeriod   账期（YYY-MM）；为空则按 periodStart 自动生成
 * @param dueDate      缴费截止日；为空 = periodStart
 * @param orgId        限定组织
 * @param houseType    限定房源类型
 * @param contractIds  限定合同；为空 = 全部生效合同
 * @param quantityOverride 覆盖数量
 * @param dryRun       试运行
 */
public record GenerateBatchCmd(

        @NotEmpty(message = "收费项目列表不能为空")
        List<Item> items,

        @NotNull(message = "费用起始日不能为空")
        LocalDate periodStart,
        @NotNull(message = "费用截止日不能为空")
        LocalDate periodEnd,

        String billPeriod,
        LocalDate dueDate,
        Long orgId,
        String houseType,
        List<Long> contractIds,
        Integer quantityOverride,
        Boolean dryRun
) {
    /** 每个收费项目可单独指定规则。 */
    public record Item(@NotNull(message = "收费项目ID不能为空") Long feeItemId, Long ruleId) {
    }
}
'''

FILES['fin/dto/GenerateBatchVO.java'] = '''package com.yundao.bp.fin.dto;

import java.math.BigDecimal;
import java.util.List;

/**
 * 多项目批量出账汇总。
 *
 * @param batchNo    批次号（便于审计与追溯）
 * @param totalGenerated 全部项目合计生成张数
 * @param totalSkipped   合计跳过张数
 * @param totalAmount    合计金额
 * @param dryRun         是否试运行
 * @param results        各项目明细结果
 */
public record GenerateBatchVO(
        String batchNo,
        int totalGenerated,
        int totalSkipped,
        BigDecimal totalAmount,
        boolean dryRun,
        List<ItemResult> results
) {
    /**
     * @param feeItemId   收费项目
     * @param feeItemName 项目名称
     * @param status      OK / FAILED
     * @param error       失败原因
     * @param detail      该项目的出账明细
     */
    public record ItemResult(Long feeItemId, String feeItemName, String status, String error,
                             GenerateResultVO detail) {
    }
}
'''

# 扩展服务接口
p1 = os.path.join(BASE, r'fin\service\BillGenerationService.java')
s1 = io.open(p1, encoding='utf-8').read()
if 'generateBatch' not in s1:
    s1 = s1.replace(
        'import com.yundao.bp.fin.dto.GenerateBillsCmd;',
        'import com.yundao.bp.fin.dto.GenerateBatchCmd;\n'
        'import com.yundao.bp.fin.dto.GenerateBatchVO;\n'
        'import com.yundao.bp.fin.dto.GenerateBillsCmd;', 1)
    s1 = s1.replace(
        '    GenerateResultVO generate(GenerateBillsCmd cmd);',
        '''    GenerateResultVO generate(GenerateBillsCmd cmd);

    /**
     * 多项目批量出账：一次跑多个收费项目（如租金 + 物业费）。
     *
     * <p>项目间相互隔离：某项目失败不影响其它项目，结果里逐项返回。
     */
    GenerateBatchVO generateBatch(GenerateBatchCmd cmd);''', 1)
    io.open(p1, 'w', encoding='utf-8').write(s1)
    print('  ~ BillGenerationService 增加 generateBatch')

# 实现
p2 = os.path.join(BASE, r'fin\service\impl\BillGenerationServiceImpl.java')
s2 = io.open(p2, encoding='utf-8').read()
if 'generateBatch' not in s2:
    s2 = s2.replace(
        'import com.yundao.bp.fin.dto.GenerateBillsCmd;',
        'import com.yundao.bp.fin.dto.GenerateBatchCmd;\n'
        'import com.yundao.bp.fin.dto.GenerateBatchVO;\n'
        'import com.yundao.bp.fin.dto.GenerateBillsCmd;', 1)

    method = '''    @Override
    @Transactional(rollbackFor = Exception.class)
    public GenerateBatchVO generateBatch(GenerateBatchCmd cmd) {
        boolean dryRun = cmd.dryRun() != null && cmd.dryRun();
        String batchNo = "GB" + System.currentTimeMillis();

        List<GenerateBatchVO.ItemResult> results = new ArrayList<>();
        int totalGenerated = 0;
        int totalSkipped = 0;
        BigDecimal totalAmount = BigDecimal.ZERO;

        for (GenerateBatchCmd.Item it : cmd.items()) {
            FinFeeItem item = feeItemMapper.selectById(it.feeItemId());
            String name = item == null ? String.valueOf(it.feeItemId()) : item.getItemName();
            try {
                // 单项目出账复用既有幂等逻辑
                GenerateResultVO one = generate(new GenerateBillsCmd(
                        it.feeItemId(), it.ruleId(),
                        cmd.periodStart(), cmd.periodEnd(),
                        cmd.billPeriod(), cmd.dueDate(),
                        cmd.orgId(), cmd.houseType(), cmd.contractIds(),
                        cmd.quantityOverride(), cmd.dryRun()));
                results.add(new GenerateBatchVO.ItemResult(it.feeItemId(), name, "OK", null, one));
                totalGenerated += one.generated();
                totalSkipped += one.skipped();
                totalAmount = totalAmount.add(one.totalAmount());
            } catch (Exception e) {
                // 项目间隔离：单项失败不影响其它项目
                log.warn("批量出账：项目 {}（{}）失败：{}", it.feeItemId(), name, e.getMessage());
                results.add(new GenerateBatchVO.ItemResult(it.feeItemId(), name, "FAILED",
                        e.getMessage(), null));
            }
        }

        log.info("多项目批量出账[{}] batchNo={} 项目 {} 生成 {} 跳过 {} 合计 {}",
                dryRun ? "试运行" : "已落库", batchNo, cmd.items().size(),
                totalGenerated, totalSkipped, totalAmount);

        return new GenerateBatchVO(batchNo, totalGenerated, totalSkipped,
                totalAmount.setScale(2, RoundingMode.HALF_UP), dryRun, results);
    }

'''
    anchor = '''    /** 数量取值。 */'''
    assert anchor in s2
    s2 = s2.replace(anchor, method + anchor, 1)
    io.open(p2, 'w', encoding='utf-8').write(s2)
    print('  ~ BillGenerationServiceImpl 增加 generateBatch')

# 控制器
p3 = os.path.join(BASE, r'fin\controller\BillGenerationController.java')
s3 = io.open(p3, encoding='utf-8').read()
if 'generateBatch' not in s3:
    s3 = s3.replace(
        'import com.yundao.bp.fin.dto.GenerateBillsCmd;',
        'import com.yundao.bp.fin.dto.GenerateBatchCmd;\n'
        'import com.yundao.bp.fin.dto.GenerateBatchVO;\n'
        'import com.yundao.bp.fin.dto.GenerateBillsCmd;', 1)
    s3 = s3.replace(
        '''    @PostMapping("/bills/generate")
    public R<GenerateResultVO> generate(@Valid @RequestBody GenerateBillsCmd cmd) {
        return R.ok(service.generate(cmd));
    }''',
        '''    @PostMapping("/bills/generate")
    public R<GenerateResultVO> generate(@Valid @RequestBody GenerateBillsCmd cmd) {
        return R.ok(service.generate(cmd));
    }

    /**
     * 多项目批量出账（一次生成租金 + 物业费等多张账单）。
     *
     * <p>项目间相互隔离，单项失败不影响其它项，结果逐项返回。
     */
    @PostMapping("/bills/generate-batch")
    public R<GenerateBatchVO> generateBatch(@Valid @RequestBody GenerateBatchCmd cmd) {
        return R.ok(service.generateBatch(cmd));
    }''', 1)
    io.open(p3, 'w', encoding='utf-8').write(s3)
    print('  ~ BillGenerationController 增加 generate-batch')

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('新增 %d 个文件' % count)
