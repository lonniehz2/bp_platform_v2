# -*- coding: utf-8 -*-
"""把同住人接入补贴按人计费（替换"默认 1 人"的凑合实现）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
p = os.path.join(BASE, r'fin\service\impl\SubsidyServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if 'cohabitantMapper' in s:
    print('已接入，跳过')
    raise SystemExit

# 1) import + 字段
s = s.replace('import com.yundao.bp.biz.entity.BizContract;',
              'import com.yundao.bp.biz.entity.BizContract;\n'
              'import com.yundao.bp.biz.entity.BizContractCohabitant;\n'
              'import com.yundao.bp.biz.mapper.BizContractCohabitantMapper;', 1)

s = s.replace('''    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;''',
              '''    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;
    /** 同住人 Mapper（用于按人补贴的保障人口计算） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private BizContractCohabitantMapper cohabitantMapper;''', 1)

# 2) 替换"默认 1 人"为真实保障人口
old = '''        // 合同表暂无同住人数字段（bp_biz_contract_cohabitant 未实现），
        // 按人补贴时需显式传入 personCount；未传按 1 人计并给出提示
        int persons;
        if (personIn != null && personIn > 0) {
            persons = personIn;
        } else {
            persons = 1;
            log.warn("按人补贴未提供家庭人口，按 1 人计算（合同 {}）", ct.getContractNo());
        }'''
new = '''        // 保障人口 = 承租人 1 人 + 同住人数（决策 D24）
        // 优先用显式传入值；否则从合同同住人表现算；同住人表不可用时兜底 1 人
        int persons;
        if (personIn != null && personIn > 0) {
            persons = personIn;
        } else {
            persons = householdSize(ct);
        }'''
assert old in s, '锚点缺失'
s = s.replace(old, new, 1)

# 3) 新增 householdSize 方法（放在 money() 前面）
anchor = '''    private static BigDecimal money(BigDecimal v) {'''
helper = '''    /**
     * 保障人口 = 承租人 1 + 同住人数。
     *
     * <p>同住人表（{@code bp_biz_contract_cohabitant}）是保障房的关键数据，
     * 按人补贴、年审人均收入核查都依赖它。
     */
    private int householdSize(BizContract ct) {
        if (cohabitantMapper == null) {
            log.warn("同住人组件不可用，按人补贴按 1 人计（合同 {}）", ct.getContractNo());
            return 1;
        }
        Long n = cohabitantMapper.selectCount(
                new LambdaQueryWrapper<BizContractCohabitant>()
                        .eq(BizContractCohabitant::getContractId, ct.getId()));
        int size = 1 + (n == null ? 0 : n.intValue());
        log.debug("合同 {} 保障人口 = 1(承租人) + {}(同住人) = {}",
                ct.getContractNo(), size - 1, size);
        return size;
    }

''' + anchor
assert anchor in s
s = s.replace(anchor, helper, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ 补贴按人计费已接入同住人')
