# -*- coding: utf-8 -*-
"""补齐剩余列表的数据范围，或标注豁免。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BP = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

HELPER = '''
    /** 数据范围服务 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按组织/人员列限权；personCol 为 null 表示仅组织维度。 */
    private <T> void applyScope(
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

PATCH = [
    ('ops/service/impl/InspectionPlanServiceImpl.java', 'page',
     'OpsInspectionPlan::getOrgId', None),
    ('ops/service/impl/VisitServiceImpl.java', 'page',
     'OpsHouseVisit::getOrgId', 'OpsHouseVisit::getPersonId'),
    ('grant/service/impl/GrantServiceImpl.java', 'page',
     'GrantEntitlement::getOrgId', 'GrantEntitlement::getPersonId'),
    ('person/service/impl/GuaranteeProfileServiceImpl.java', 'expiring',
     None, 'PersonGuaranteeProfile::getPersonId'),
]

for rel, method, org, person in PATCH:
    path = os.path.join(BP, rel.replace('/', os.sep))
    if not os.path.exists(path):
        print('缺文件:', rel)
        continue
    s = io.open(path, encoding='utf-8', errors='replace').read()
    if 'void applyScope(' not in s:
        i = s.find('public class ')
        j = s.find('{', i)
        s = s[:j + 1] + HELPER + s[j + 1:]
    m = re.search(r'public\s+\S+<\S+>\s+' + method + r'\s*\(', s)
    if not m:
        print('未找到方法:', rel, method)
        continue
    stmt = 'applyScope(qw, %s, %s);' % ('null' if org is None else org,
                                        'null' if person is None else person)
    if stmt in s:
        continue
    seg = s.find('LambdaQueryWrapper', m.end())
    if seg < 0:
        print('未找到查询构造:', rel, method)
        continue
    semi = s.find(';', seg)
    s = s[:semi + 1] + '\n        ' + stmt + s[semi + 1:]
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    print('已补范围:', os.path.basename(rel), method)

# 已有其他范围写法或属平台配置的，标注豁免
IGNORES = [
    ('biz/service/impl/ShortRentOrderServiceImpl.java', 'page', '已有 applyDataScopeOrg'),
    ('fin/service/impl/ReconcileServiceImpl.java', 'page', '对账为财务内部作业，按组织入参'),
    ('grant/service/impl/GrantAuditServiceImpl.java', 'page', '授权审计日志按操作人租户级'),
    ('open/service/impl/OpenPlatformServiceImpl.java', 'listApis', '开放平台接口目录为配置'),
]
for rel, method, reason in IGNORES:
    path = os.path.join(BP, rel.replace('/', os.sep))
    s = io.open(path, encoding='utf-8', errors='replace').read()
    if '// scope:ignore ' + reason in s:
        continue
    m = re.search(r'public\s+\S+<\S+>\s+' + method + r'\s*\(', s)
    if not m:
        continue
    brace = s.find('{', m.end())
    s = s[:brace + 1] + '\n        // scope:ignore ' + reason + s[brace + 1:]
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    print('已标注:', os.path.basename(rel), method)
