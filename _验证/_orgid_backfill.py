# -*- coding: utf-8 -*-
"""给退租与押金补 org_id，补齐数据范围四档。

步骤：
1) DDL：bp_biz_termination / bp_fin_deposit 增加 org_id（幂等）
2) 回填：按 contract_id 从 bp_biz_contract.org_id 回填
3) 实体加字段（Lombok 自动生成访问器）
4) 建单处写入 orgId（从合同取）
5) 服务改为四档过滤（full=true）
"""
import io
import os

import pymysql

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- 1) DDL + 回填 ----------
conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()
for table in ('bp_biz_termination', 'bp_fin_deposit'):
    cur.execute("show columns from %s like 'org_id'" % table)
    if not cur.fetchone():
        cur.execute('alter table %s add column org_id bigint null comment "所属组织（数据范围过滤）"' % table)
        print('%s：已加 org_id' % table)
    else:
        print('%s：已有 org_id' % table)
    cur.execute('''update %s t join bp_biz_contract c on c.id = t.contract_id
                   set t.org_id = c.org_id
                   where t.org_id is null''' % table)
    print('  回填 %d 行' % cur.rowcount)
conn.commit()
cur.execute('select count(*) from bp_biz_termination where org_id is null')
print('退租空 org_id：%d' % cur.fetchone()[0])
cur.execute('select count(*) from bp_fin_deposit where org_id is null')
print('押金空 org_id：%d' % cur.fetchone()[0])
conn.close()

# ---------- 2) 实体加字段 ----------
E1 = os.path.join(J, 'biz', 'entity', 'BizTermination.java')
s = io.open(E1, encoding='utf-8').read()
if 'private Long orgId;' not in s:
    s = s.replace('    private Long contractId;',
                  '    /** 所属组织（数据范围过滤用） */\n    private Long orgId;\n\n    private Long contractId;', 1)
    io.open(E1, 'w', encoding='utf-8', newline='').write(s)
    print('BizTermination：已加 orgId')

E2 = os.path.join(J, 'fin', 'entity', 'FinDeposit.java')
s = io.open(E2, encoding='utf-8').read()
if 'private Long orgId;' not in s:
    s = s.replace('    private Long contractId;',
                  '    /** 所属组织（数据范围过滤用） */\n    private Long orgId;\n\n    private Long contractId;', 1)
    io.open(E2, 'w', encoding='utf-8', newline='').write(s)
    print('FinDeposit：已加 orgId')

# ---------- 3) 建单写入 orgId ----------
def patch_create(path, anchor_line='e.setContractId(cmd.contractId());'):
    p = os.path.join(J, *path.split('/'))
    s = io.open(p, encoding='utf-8').read()
    if 'setOrgId(' in s and 'contractOrgId' in s:
        print('%s 已写入组织' % path)
        return
    inject = (anchor_line + '\n'
              '        // 组织取自合同，供数据范围（ORG/ORG_SUB）过滤\n'
              '        if (contractOrgIdMapper != null) {\n'
              '            com.yundao.bp.biz.entity.BizContract c = contractOrgIdMapper.selectById(cmd.contractId());\n'
              '            if (c != null) {\n'
              '                e.setOrgId(c.getOrgId());\n'
              '            }\n'
              '        }')
    if anchor_line not in s:
        print('%s 未找到建单锚点' % path)
        return
    s = s.replace(anchor_line, inject, 1)
    # 注入合同 mapper
    inject_field = '''
    /** 合同（取组织用于数据范围过滤） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizContractMapper contractOrgIdMapper;
'''
    idx = s.find('    public ')
    s = s[:idx] + inject_field + '\n' + s[idx:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s 已写入组织' % path)


patch_create('biz/service/impl/TerminationServiceImpl.java')
patch_create('fin/service/impl/DepositRefundServiceImpl.java')

# ---------- 4) 过滤改为四档 ----------
for path, entity, org_getter, person_getter in [
        ('biz/service/impl/TerminationServiceImpl.java', 'BizTermination', 'getOrgId', 'getPersonId'),
        ('fin/service/impl/DepositRefundServiceImpl.java', 'FinDeposit', 'getOrgId', 'getPersonId')]:
    p = os.path.join(J, *path.split('/'))
    s = io.open(p, encoding='utf-8').read()
    old = 'applyDataScope(qw, %s::%s, %s::%s, false);' % (entity, org_getter, entity, person_getter)
    new = 'applyDataScope(qw, %s::%s, %s::%s, true);' % (entity, org_getter, entity, person_getter)
    if old in s:
        s = s.replace(old, new, 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        print('%s：过滤改为四档' % path)
