# -*- coding: utf-8 -*-
"""修正：合同无同住人数字段，按人补贴默认 1 人（可显式传入）"""
import io

p = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\fin\service\impl\SubsidyServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

old = '''        int persons = personIn == null || personIn <= 0
                ? (ct.getCohabitantCount() == null || ct.getCohabitantCount() <= 0
                ? 1 : ct.getCohabitantCount()) : personIn;'''
new = '''        // 合同表暂无同住人数字段（bp_biz_contract_cohabitant 未实现），
        // 按人补贴时需显式传入 personCount；未传按 1 人计并给出提示
        int persons;
        if (personIn != null && personIn > 0) {
            persons = personIn;
        } else {
            persons = 1;
            log.warn("按人补贴未提供家庭人口，按 1 人计算（合同 {}）", ct.getContractNo());
        }'''
assert old in s, 'anchor missing'
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('已修正：按人补贴默认 1 人')
