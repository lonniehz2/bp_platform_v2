# -*- coding: utf-8 -*-
"""物业：公摊费用分摊出账（新增能力）。

场景：小区公共区域水电、电梯维保等总费用，按「建筑面积」或「户数」分摊到各房源，
      为每套在租房屋生成一张账单（payer 取该房源当前履约合同的承租人）。

接口：POST /fin/bills/generate-shared
  入参：orgId, spaceId(可选，限某楼栋), feeItemId, totalAmount, periodStart/End,
        billPeriod, dueDate, allocateBy = AREA | HOUSE
返回：生成账单数与分摊明细摘要
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

# ---------- 1) Controller ----------
C = os.path.join(J, 'controller', 'BillingController.java')
s = io.open(C, encoding='utf-8').read()
if 'generate-shared' not in s:
    block = '''
    /**
     * 公摊费用分摊出账（物业管理场景）。
     *
     * <p>把公共区域总费用按建筑面积或户数分摊到在租房源，为每套生成一张账单。
     */
    @PostMapping("/bills/generate-shared")
    @RequirePerm("fin:bill:create")
    public R<java.util.Map<String, Object>> generateShared(
            @Valid @RequestBody com.yundao.bp.fin.dto.SharedBillCmd cmd) {
        return R.ok(billingService.generateSharedBills(cmd));
    }
'''
    anchor = '    @PostMapping("/bills")'
    if anchor in s:
        s = s.replace(anchor, block + '\n' + anchor, 1)
    else:
        i = s.rstrip().rfind('}')
        s = s[:i] + block + s[i:]
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('BillingController：/bills/generate-shared 已加')

# ---------- 2) Cmd ----------
P = os.path.join(J, 'dto', 'SharedBillCmd.java')
if not os.path.exists(P):
    io.open(P, 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 公摊费用分摊出账。
 *
 * @param allocateBy 分摊方式：AREA（按建筑面积）| HOUSE（按户数）
 */
public record SharedBillCmd(

        @NotNull(message = "组织不能为空")
        Long orgId,

        /** 限定楼栋/单元（可空，空表示整个组织） */
        Long spaceId,

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        @NotNull(message = "总分摊金额不能为空")
        @DecimalMin(value = "0.01", message = "分摊金额必须大于 0")
        BigDecimal totalAmount,

        @NotNull(message = "费用起始日不能为空")
        LocalDate periodStart,

        @NotNull(message = "费用截止日不能为空")
        LocalDate periodEnd,

        @NotBlank(message = "账期不能为空")
        String billPeriod,

        LocalDate dueDate,

        /** AREA | HOUSE */
        String allocateBy
) {
}
''', )
    print('SharedBillCmd：已创建')

# ---------- 3) Service 接口 ----------
S = os.path.join(J, 'service', 'BillingService.java')
s = io.open(S, encoding='utf-8').read()
if 'generateSharedBills' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + ('\n    /** 公摊费用分摊出账。 */\n'
                 '    java.util.Map<String, Object> generateSharedBills(\n'
                 '            com.yundao.bp.fin.dto.SharedBillCmd cmd);\n') + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('BillingService：generateSharedBills 已加')

print('完成（实现需在 BillingServiceImpl 中补齐）')
