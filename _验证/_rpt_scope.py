# -*- coding: utf-8 -*-
"""报表数据范围收口：查询与导出统一按用户数据范围限定 orgId。

规则：
  ALL     按请求的 orgId（可为空＝全量）
  ORG     强制为本组织；请求他组织时自动改成本组织
  ORG_SUB 请求组织在本组织子树内则允许，否则回落本组织
  SELF    拒绝（报表是组织级聚合，仅本人的角色无报表权限）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'rpt', 'service', 'impl', 'ReportServiceImpl.java')

s = io.open(P, encoding='utf-8').read()

# 1) 注入 DataScopeService
if 'dataScopeService' not in s:
    inject = '''
    /** 数据范围（报表查询/导出按此限定组织） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /**
     * 计算报表实际使用的组织范围。
     *
     * <p>报表是组织级聚合数据，越权导出等于批量泄露，因此在这里统一收口：
     * 非 ALL 角色不能跨组织取数，SELF 角色直接拒绝。
     */
    private Long resolveReportOrg(Long requested) {
        if (dataScopeService == null) {
            return requested;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return requested;
        }
        if (scope.isSelf()) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid(
                    "当前角色数据范围为「仅本人」，无报表查看/导出权限，请联系管理员");
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            if (requested == null || scope.orgIds().contains(requested)) {
                return requested == null ? scope.orgId() : requested;
            }
            return scope.orgId();
        }
        // ORG：强制本组织
        return scope.orgId() == null ? requested : scope.orgId();
    }
'''
    idx = s.find('    public ReportServiceImpl(')
    if idx < 0:
        idx = s.find('    public ', s.find('class '))
    s = s[:idx] + inject + '\n' + s[idx:]

# 2) query 使用 resolveReportOrg
old_q = 'List<Map<String, Object>> rows = rowsOf(def.getReportCode(), cmd.orgId());'
if old_q in s:
    s = s.replace(old_q,
                  'List<Map<String, Object>> rows = rowsOf(def.getReportCode(),\n'
                  '                resolveReportOrg(cmd.orgId()));')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('ReportServiceImpl：已接入数据范围（query/export 共 %d 处）' % s.count('resolveReportOrg(cmd.orgId())'))
