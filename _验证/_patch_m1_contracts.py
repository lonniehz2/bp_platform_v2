# -*- coding: utf-8 -*-
import io

# 合同创建：初始化计费人口/床位
p = r'..\backend\src\main\java\com\yundao\bp\biz\service\impl\ContractServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
if 'setBillingPersonCount' not in s:
    s = s.replace('''        e.setActualPay(actualPay);''',
                  '''        e.setActualPay(actualPay);
        e.setBillingPersonCount(1);
        e.setBillingBedCount(1);
        e.setQuantityUpdatedAt(LocalDateTime.now());''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('contract init counts')

# 同住人增删：刷新合同计费人口
p = r'..\backend\src\main\java\com\yundao\bp\biz\service\impl\CohabitantServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
if 'refreshPersonCount' not in s:
    s = s.replace('''        mapper.insert(e);''', '''        mapper.insert(e);
        refreshPersonCount(contractId);''', 1)
    s = s.replace('''        mapper.deleteById(id);''', '''        BizContractCohabitant row = mapper.selectById(id);
        mapper.deleteById(id);
        if (row != null) {
            refreshPersonCount(row.getContractId());
        }''', 1)
    idx = s.rfind('}')
    s = s[:idx] + '''
    /** 同住人变化后刷新合同计费人口（承租人 1 + 同住人数）。 */
    private void refreshPersonCount(Long contractId) {
        if (contractId == null) {
            return;
        }
        BizContract c = contractMapper.selectById(contractId);
        if (c == null) {
            return;
        }
        Long n = mapper.selectCount(new com.baomidou.mybatisplus.core.conditions.query
                .LambdaQueryWrapper<BizContractCohabitant>()
                .eq(BizContractCohabitant::getContractId, contractId));
        c.setBillingPersonCount(1 + (n == null ? 0 : n.intValue()));
        if (c.getBillingBedCount() == null) {
            c.setBillingBedCount(1);
        }
        c.setQuantityUpdatedAt(java.time.LocalDateTime.now());
        contractMapper.updateById(c);
    }
''' + s[idx:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('cohabitant refresh count')

# 换房新合同：继承计费人口/床位
p = r'..\backend\src\main\java\com\yundao\bp\biz\service\impl\ExchangeServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
if 'setBillingPersonCount' not in s:
    s = s.replace('''        nc.setActualPay(oldCt.getActualPay());''',
                  '''        nc.setActualPay(oldCt.getActualPay());
        nc.setBillingPersonCount(oldCt.getBillingPersonCount());
        nc.setBillingBedCount(oldCt.getBillingBedCount() == null ? 1 : oldCt.getBillingBedCount());
        nc.setQuantityUpdatedAt(LocalDateTime.now());''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('exchange inherit counts')
