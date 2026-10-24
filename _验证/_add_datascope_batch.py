# -*- coding: utf-8 -*-
"""给缺少数据范围的业务列表补 applyDataScope。

只处理「人员/组织敏感」的列表；配置类（计费项、模板、开放平台）另行标注 ignore。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BP = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

HELPER = '''
    /** 数据范围服务（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按组织或人员列限权；personCol 传 null 表示该实体只有组织维度。 */
    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf() && personCol != null) {
            qw.eq(personCol, scope.personId() == null ? -1L : scope.personId());
            return;
        }
        if (scope.isSelf()) {
            // 无人员列：仅本人不可见，退化为按组织
            if (scope.orgId() != null && orgCol != null) {
                qw.eq(orgCol, scope.orgId());
            } else {
                qw.apply("1 = 0");
            }
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty() && orgCol != null) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null && orgCol != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }
'''

# 文件 → (实体类简名, 方法名, org 列表达式, person 列表达式)
TARGETS = [
    ('person/service/impl/GuaranteeProfileServiceImpl.java',
     'PersonGuaranteeProfile', 'page', None, 'PersonGuaranteeProfile::getPersonId'),
    ('person/service/impl/GuaranteeProfileServiceImpl.java',
     'PersonGuaranteeProfile', 'expiring', None, 'PersonGuaranteeProfile::getPersonId'),
    ('person/service/impl/VerifyRecordServiceImpl.java',
     'PersonVerifyRecord', 'page', None, 'PersonVerifyRecord::getPersonId'),
    ('grant/service/impl/KeyringServiceImpl.java',
     'GrantKeyring', 'page', None, 'GrantKeyring::getPersonId'),
    ('biz/service/impl/ShortRentOrderServiceImpl.java',
     'ShortRentOrder', 'page', 'ShortRentOrder::getOrgId', None),
    ('fin/service/impl/BillingServiceImpl.java',
     'FinPayment', 'pagePayments', 'FinPayment::getOrgId', 'FinPayment::getPersonId'),
    ('ops/service/impl/AlertServiceImpl.java',
     'OpsAlert', 'page', 'OpsAlert::getOrgId', 'OpsAlert::getPersonId'),
    ('ops/service/impl/ComplaintServiceImpl.java',
     'OpsComplaint', 'page', 'OpsComplaint::getOrgId', 'OpsComplaint::getPersonId'),
    ('fin/service/impl/ReconcileServiceImpl.java',
     'FinReconcile', 'page', 'FinReconcile::getOrgId', None),
]

touched = set()
for rel, entity, method, org, person in TARGETS:
    path = os.path.join(BP, rel.replace('/', os.sep))
    if not os.path.exists(path):
        print('缺文件:', rel)
        continue
    s = io.open(path, encoding='utf-8', errors='replace').read()
    changed = False
    if 'applyDataScope' not in s:
        i = s.find('public class ')
        j = s.find('{', i)
        s = s[:j + 1] + HELPER + s[j + 1:]
        changed = True
    # 在该方法的查询构造后插入调用
    m = re.search(r'public\s+PageResult<[^>]+>\s+' + method + r'\s*\(', s)
    if not m:
        m = re.search(r'public\s+List<[^>]+>\s+' + method + r'\s*\(', s)
    if m:
        seg_start = s.find('LambdaQueryWrapper', m.end())
        if seg_start > 0:
            semi = s.find(';', seg_start)
            if semi > 0:
                cols = 'null' if org is None else org
                args = '%s, %s' % (cols, 'null' if person is None else person)
                if ('applyDataScope(qw, %s)' % args) not in s:
                    s = s[:semi + 1] + '\n        applyDataScope(qw, %s);' % args + s[semi + 1:]
                    changed = True
    if changed:
        io.open(path, 'w', encoding='utf-8', newline='').write(s)
        touched.add(rel)
        print('已补范围:', rel, method)

print('共处理文件:', len(touched))
