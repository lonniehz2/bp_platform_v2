# -*- coding: utf-8 -*-
"""ContractVO 补 parentContractId（换房/续签追溯链条）"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp\biz\dto\ContractVO.java'
s = io.open(p, encoding='utf-8').read()

if 'parentContractId' in s:
    print('已存在，跳过')
    raise SystemExit

# 1) 记录组件：末尾追加
old_field = '''        LocalDateTime createTime
) {'''
new_field = '''        LocalDateTime createTime,
        /** 父合同ID：换房/续签生成的新合同指向原合同，便于追溯链条 */
        Long parentContractId
) {'''
assert old_field in s, '字段锚点缺失'
s = s.replace(old_field, new_field, 1)

# 2) from() 构造：末尾追加
old_call = '''                daysToExpire, expiringSoon, st.isOccupying(), e.getRemark(), e.getCreateTime());'''
new_call = '''                daysToExpire, expiringSoon, st.isOccupying(), e.getRemark(), e.getCreateTime(),
                e.getParentContractId());'''
assert old_call in s, '构造锚点缺失'
s = s.replace(old_call, new_call, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ ContractVO 已补 parentContractId')
