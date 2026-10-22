# -*- coding: utf-8 -*-
"""数据范围第三批：门禁记录（组织+人员，隐私敏感）与押金（仅人员档）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

INJECT = '''
    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按数据范围追加条件（full=true 时组织也过滤）。 */
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
            return;     // 无组织列时，ORG/ORG_SUB 不额外限制
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
    ('dev/service/impl/AccessRecordServiceImpl.java',
     'LambdaQueryWrapper<DevAccessRecord> qw = new LambdaQueryWrapper<DevAccessRecord>()',
     'DevAccessRecord', 'getOrgId', 'getPersonId', 'true'),
    ('fin/service/impl/DepositRefundServiceImpl.java',
     'LambdaQueryWrapper<FinDeposit> qw = new LambdaQueryWrapper<FinDeposit>()',
     'FinDeposit', 'getPersonId', 'getPersonId', 'false'),
]

for rel, anchor, entity, orgGetter, personGetter, full in TARGETS:
    p = os.path.join(J, *rel.split('/'))
    s = io.open(p, encoding='utf-8').read()
    if 'applyDataScope' in s:
        print('%s 已应用' % rel)
        continue
    if anchor not in s:
        print('%s 未找到锚点（%s）' % (rel, anchor))
        continue

    cls = os.path.basename(p).replace('.java', '').replace('Impl', '')
    idx = s.find('    public ' + cls, s.find('class '))
    if idx < 0:
        idx = s.find('public ', s.find('class ')) - 4
    s = s[:idx] + INJECT + '\n' + s[idx:]

    expr_end = s.find(';', s.find(anchor))
    call = ('\n        applyDataScope(qw, %s::%s, %s::%s, %s);'
            % (entity, orgGetter, entity, personGetter, full))
    s = s[:expr_end + 1] + call + s[expr_end + 1:]

    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s 已应用数据范围' % rel)
