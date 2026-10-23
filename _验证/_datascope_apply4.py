# -*- coding: utf-8 -*-
"""数据范围补全第二批（7 个模块）。

按实体可用列选择策略：
  组织+人员 → 四档完整
  仅人员   → SELF 生效，ORG 不额外限制
  仅组织   → ORG/ORG_SUB/SELF 生效（SELF 视为不可见）
  两者皆无 → 跳过并记录（需 join，后续处理）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

INJECT_FULL = '''
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

    /** 仅组织维度的数据范围（实体无人员列时使用）。 */
    private <T> void applyDataScopeOrg(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            qw.eq(orgCol, -1L);   // 仅本人角色无组织级数据
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

# (文件, 实体, 锚点, 调用语句, 是否已有 applyDataScope)
TARGETS = [
    ('ops/service/impl/AppealServiceImpl.java', 'BizAppeal',
     'LambdaQueryWrapper<BizAppeal> qw = new LambdaQueryWrapper<BizAppeal>()',
     'applyDataScope(qw, BizAppeal::getOrgId, BizAppeal::getPersonId, true);'),
    ('biz/service/impl/AnnualReviewServiceImpl.java', 'BizAnnualReview',
     'LambdaQueryWrapper<BizAnnualReview> qw = new LambdaQueryWrapper<BizAnnualReview>()',
     'applyDataScope(qw, BizAnnualReview::getPersonId, BizAnnualReview::getPersonId, false);'),
    ('biz/service/impl/ExchangeServiceImpl.java', 'BizExchange',
     'LambdaQueryWrapper<BizExchange> qw = new LambdaQueryWrapper<BizExchange>()',
     'applyDataScope(qw, BizExchange::getPersonId, BizExchange::getPersonId, false);'),
    ('biz/service/impl/PublicityServiceImpl.java', 'BizPublicity',
     'LambdaQueryWrapper<BizPublicity> qw = new LambdaQueryWrapper<BizPublicity>()',
     'applyDataScopeOrg(qw, BizPublicity::getOrgId);'),
    ('biz/service/impl/ShortRentOrderServiceImpl.java', 'BizShortRentOrder',
     'LambdaQueryWrapper<BizShortRentOrder> qw = new LambdaQueryWrapper<BizShortRentOrder>()',
     'applyDataScopeOrg(qw, BizShortRentOrder::getOrgId);'),
]

for rel, entity, anchor, call in TARGETS:
    p = os.path.join(J, *rel.split('/'))
    if not os.path.exists(p):
        print('%s 不存在' % rel)
        continue
    s = io.open(p, encoding='utf-8').read()
    if 'applyDataScopeOrg' in s or 'applyDataScope(qw' in s:
        print('%s 已应用' % rel)
        continue
    if anchor not in s:
        print('%s 未找到查询锚点' % rel)
        continue
    cls = os.path.basename(p).replace('.java', '').replace('Impl', '')
    idx = s.find('    public ' + cls, s.find('class '))
    if idx < 0:
        idx = s.find('public ', s.find('class ')) - 4
    s = s[:idx] + INJECT_FULL + '\n' + s[idx:]
    expr_end = s.find(';', s.find(anchor))
    s = s[:expr_end + 1] + '\n        ' + call + s[expr_end + 1:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s 已应用数据范围' % rel)

print('注意：BizCreditRecord（decideOrgId）、FinArrearsAction（contractId/personId）'
      '需单独按列名适配；BizContractChange、FinCashFlow 无组织/人员列，暂跳过。')
