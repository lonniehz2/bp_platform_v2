# -*- coding: utf-8 -*-
import io

# 合同实体字段
p = r'..\backend\src\main\java\com\yundao\bp\biz\entity\BizContract.java'
s = io.open(p, encoding='utf-8').read()
if 'billingPersonCount' not in s:
    s = s.replace('    private BigDecimal actualPay;', '''    private BigDecimal actualPay;

    /** 计费人口快照：承租人 1 + 同住人 */
    private Integer billingPersonCount;
    /** 计费床位快照 */
    private Integer billingBedCount;
    private LocalDateTime quantityUpdatedAt;''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('BizContract fields')

# 账单实体字段
p = r'..\backend\src\main\java\com\yundao\bp\fin\entity\FinBill.java'
s = io.open(p, encoding='utf-8').read()
if 'ruleSnapshot' not in s:
    s = s.replace('    private String remark;', '''    private String remark;

    /** 命中的计费规则（快照，避免规则后续变更影响历史解释） */
    private Long ruleId;
    private Integer ruleVersion;
    private String ruleSnapshot;
    /** 本单计费数量（人/床/间夜/套） */
    private Integer billingQuantity;
    private String quantityUnit;
    private String quantitySource;''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('FinBill fields')

# 出账命令增加规则方式
p = r'..\backend\src\main\java\com\yundao\bp\fin\dto\GenerateBillsCmd.java'
s = io.open(p, encoding='utf-8').read()
if 'ruleMode' not in s:
    s = s.replace('''        /** 可选：指定计费规则；不传则用项目默认单价 */
        Long ruleId,''', '''        /** 可选：指定计费规则；不传则用项目默认单价 */
        Long ruleId,

        /** 规则方式：AUTO 自动匹配（默认）/ MANUAL 指定 / NONE 不使用 */
        String ruleMode,''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('GenerateBillsCmd ruleMode')

# 合同 VO 增加计费数量
p = r'..\backend\src\main\java\com\yundao\bp\biz\dto\ContractVO.java'
s = io.open(p, encoding='utf-8').read()
if 'billingPersonCount' not in s:
    s = s.replace('        Long parentContractId', '''        Long parentContractId,
        Integer billingPersonCount,
        Integer billingBedCount''', 1)
    s = s.replace('e.getParentContractId());', 'e.getParentContractId(),\n                e.getBillingPersonCount(), e.getBillingBedCount());', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('ContractVO fields')
