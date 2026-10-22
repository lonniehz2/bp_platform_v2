# -*- coding: utf-8 -*-
"""把数据范围应用到四个核心列表查询：人员 / 房源 / 合同 / 账单。

每个服务注入 DataScopeService（可选，不破坏既有构造器），
在分页查询 wrapper 末尾追加：
  SELF    -> personId = 当前用户绑定人员（无绑定则查不到数据）
  ORG     -> orgId = 用户组织
  ORG_SUB -> orgId in 组织子树
  ALL     -> 不加条件
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

INJECT = '''
    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /**
     * 把当前用户的数据范围追加到查询条件上。
     *
     * @param qw       查询条件
     * @param orgCol   组织列（orgId）
     * @param personCol 人员列（SELF 范围用）
     */
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
        if (scope.isSelf()) {
            if (scope.personId() == null) {
                qw.eq(orgCol, -1L);      // 未绑定人员：不返回任何数据
            } else {
                qw.eq(personCol, scope.personId());
            }
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
    ('person/service/impl/PersonServiceImpl.java',
     'LambdaQueryWrapper<Person> qw = new LambdaQueryWrapper<Person>()',
     'Person', 'getOrgId', 'getId'),
    ('asset/service/impl/HouseServiceImpl.java',
     'LambdaQueryWrapper<AssetHouse> qw = new LambdaQueryWrapper<AssetHouse>()',
     'AssetHouse', 'getOrgId', 'getOwnerPersonId'),
    ('biz/service/impl/ContractServiceImpl.java',
     'LambdaQueryWrapper<BizContract> qw = new LambdaQueryWrapper<BizContract>()',
     'BizContract', 'getOrgId', 'getLesseePersonId'),
    ('fin/service/impl/BillingServiceImpl.java',
     'LambdaQueryWrapper<FinBill> qw = new LambdaQueryWrapper<FinBill>()',
     'FinBill', 'getOrgId', 'getPersonId'),
]

for rel, anchor, entity, orgGetter, personGetter in TARGETS:
    p = os.path.join(J, *rel.split('/'))
    s = io.open(p, encoding='utf-8').read()
    if 'applyDataScope' in s:
        print('%s 已应用' % rel)
        continue
    if anchor not in s:
        print('%s 未找到查询锚点' % rel)
        continue

    # 注入方法与字段：放在类里第一个 public 构造器/方法之前
    idx = s.find('    public ' + os.path.basename(p).replace('.java', '').split('Impl')[0],
                 s.find('class '))
    if idx < 0:
        idx = s.find('public ', s.find('class ')) - 4
    s = s[:idx] + INJECT + '\n' + s[idx:]

    # 在 wrapper 创建后追加范围条件（找到该 wrapper 的 .orderBy 或 ; 结尾）
    line_end = s.find('\n', s.find(anchor))
    # 向前找该 wrapper 链式表达式的结尾（以 .orderBy... 或分号结尾的分号）
    expr_end = s.find(';', line_end)
    call = ('\n        applyDataScope(qw, %s::%s, %s::%s);'
            % (entity, orgGetter, entity, personGetter))
    s = s[:expr_end + 1] + call + s[expr_end + 1:]

    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('%s 已应用数据范围' % rel)
