# -*- coding: utf-8 -*-
import io

# 1) 账单：只按合同月租计应收，补贴由“补贴发放-抵扣租金”冲减，避免重复抵扣
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\BillGenerationServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
old = '''                amount = money(ct.getMonthlyRent().multiply(pro.months()));
                BigDecimal subsidy = ct.getSubsidyAmount() == null
                        ? BigDecimal.ZERO : ct.getSubsidyAmount();
                discount = money(subsidy.multiply(pro.months()));
                if (discount.compareTo(amount) > 0) {
                    discount = amount;
                }
                calcExplain = "合同月租 " + ct.getMonthlyRent().toPlainString()
                        + " × " + pro.months().stripTrailingZeros().toPlainString() + " 个月"
                        + (discount.compareTo(BigDecimal.ZERO) > 0
                        ? "；补贴抵扣 " + discount.toPlainString() : "");'''
new = '''                amount = money(ct.getMonthlyRent().multiply(pro.months()));
                calcExplain = "合同月租 " + ct.getMonthlyRent().toPlainString()
                        + " × " + pro.months().stripTrailingZeros().toPlainString() + " 个月";'''
if old not in s:
    raise SystemExit('billing subsidy block not found')
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('billing now uses contract rent only')

# 2) 补贴：兼容 OFFSET / OFFSET_RENT 两种发放方式
p = r'..\backend\src\main\java\com\yundao\bp\fin\service\impl\SubsidyServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
old = '''        if ("OFFSET_RENT".equals(e.getPayMode())) {'''
new = '''        if ("OFFSET".equals(e.getPayMode()) || "OFFSET_RENT".equals(e.getPayMode())) {'''
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('subsidy offset accepts OFFSET')

# 3) 换房批准：申请中 → 审批中 → 已批准，一步完成
p = r'..\backend\src\main\java\com\yundao\bp\biz\service\impl\ExchangeServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
old = '''    public ExchangeVO approve(Long id, String opinion) {
        BizExchange e = require(id);
        transition(e, ExchangeStatus.APPROVED);'''
new = '''    public ExchangeVO approve(Long id, String opinion) {
        BizExchange e = require(id);
        // 申请中可直接批准：内部先流转到审批中，再批准
        if (ExchangeStatus.APPLYING.name().equals(e.getExchangeStatus())) {
            transition(e, ExchangeStatus.APPROVING);
        }
        transition(e, ExchangeStatus.APPROVED);'''
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('exchange approve auto-submits')

# 4) 前端：换房接口路径去掉重复 /api/v1
p = r'..\frontend\src\views\Exchanges.vue'
s = io.open(p, encoding='utf-8').read()
for suffix in ('submit', 'approve', 'reject', 'complete', 'no-exchange'):
    s = s.replace("'/api/v1/exchanges/{id}/" + suffix + "'", "'/exchanges/{id}/" + suffix + "'")
# watch 必须在 form 声明之后（否则 setup 期间访问未初始化变量，自动带出逻辑失效）
s = s.replace("watch(() => form.personId, (pid) => fillFromPerson(pid))\n", "", 1)
s = s.replace('''  forceExchange: false
})''', '''  forceExchange: false
})

watch(() => form.personId, (pid) => fillFromPerson(pid))''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('exchanges paths and watch fixed')

# 5) 发放方式枚举补 BANK
p = r'..\frontend\src\constants\enums.js'
s = io.open(p, encoding='utf-8').read()
if "BANK: '银行代发'" not in s:
    s = s.replace("    OFFSET: '抵扣房租',", "    BANK: '银行代发',\n    OFFSET: '抵扣房租',", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('BANK label added')
