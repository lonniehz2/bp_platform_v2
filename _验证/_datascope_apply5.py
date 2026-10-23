# -*- coding: utf-8 -*-
"""数据范围补全第三批：申诉、信用惩戒、催缴（按实体实际列名适配）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

INJECT = '''
    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol,
            boolean full) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            if (scope.personId() == null) {
                qw.eq(personCol, -1L);
            } else {
                qw.eq(personCol, scope.personId());
            }
            return;
        }
        if (!full) {
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }
'''

TARGETS = [
    # 申诉：orgId + personId
    ('biz/service/impl/AppealServiceImpl.java', 'AppealServiceImpl',
     'LambdaQueryWrapper<BizAppeal> qw = new LambdaQueryWrapper<BizAppeal>()',
     'applyDataScope(qw, BizAppeal::getOrgId, BizAppeal::getPersonId, true);'),
    # 信用惩戒：decideOrgId + personId
    ('biz/service/impl/CreditServiceImpl.java', 'CreditServiceImpl',
     'LambdaQueryWrapper<BizCreditRecord> qw = new LambdaQueryWrapper<BizCreditRecord>()',
     'applyDataScope(qw, BizCreditRecord::getDecideOrgId, BizCreditRecord::getPersonId, true);'),
    # 催缴：仅 personId（无组织列）
    ('fin/service/impl/ArrearsActionServiceImpl.java', 'ArrearsActionServiceImpl',
     'LambdaQueryWrapper<FinArrearsAction> qw = new LambdaQueryWrapper<FinArrearsAction>()',
     'applyDataScope(qw, FinArrearsAction::getPersonId, FinArrearsAction::getPersonId, false);'),
]

for rel, cls, anchor, call in TARGETS:
    p = os.path.join(J, *rel.split('/'))
    s = io.open(p, encoding='utf-8').read()
    if 'applyDataScope(qw' in s:
        print('%s 已应用' % rel)
        continue
    if anchor not in s:
        print('%s 未找到锚点（实际查询可能不是该实体）' % rel)
        continue
    idx = s.find('    public ' + cls, s.find('class '))
    if idx < 0:
        idx = s.find('public ', s.find('class ')) - 4
    s = s[:idx] + INJECT + '\n' + s[idx:]
    expr_end = s.find(';', s.find(anchor))
    s = s[:expr_end + 1] + '\n        ' + call + s[expr_end + 1:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s 已应用数据范围' % rel)
