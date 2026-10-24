# -*- coding: utf-8 -*-
"""数据范围守护扫描：返回列表的 Service 方法必须带数据范围过滤。

规则
----
扫描 `service/impl/*ServiceImpl.java` 中**对外列表方法**（名字以
page/list/search/query/records/history/expiring/tree/children/subtree 开头），
若方法体内直接查库（selectPage / selectList）却没有任何范围过滤，则报警。

通过条件（三者其一）：
  * `applyDataScope(`            标准数据范围（ALL/ORG_SUB/ORG/SELF）
  * `applyXxxScope(`             领域专用范围（如 applyWaitingScope）
  * `dataScopeService.current()` 自行处理

自动豁免
--------
1. **按父级限权**：参数里带业务 ID（contractId / parentId / batchId ...），
   查询天然被父对象限定。
2. **公共数据**：字典、参数、权限、区划、菜单等全局表（IGNORE_CLASSES）。
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BACKEND = os.path.join(ROOT, 'backend', 'src', 'main', 'java')

IGNORE_CLASSES = {
    'SysRegionServiceImpl', 'SysDictServiceImpl', 'SysParamServiceImpl',
    'PermissionServiceImpl', 'RoleServiceImpl', 'MenuServiceImpl',
    'IamOrgServiceImpl', 'OpenAppServiceImpl', 'GovReportServiceImpl',
    'SysLogServiceImpl', 'AuthServiceImpl', 'AuditServiceImpl',
    'ConfigServiceImpl', 'DictServiceImpl', 'FileServiceImpl',
    'MetricServiceImpl', 'ScreenServiceImpl', 'RuleEngineServiceImpl',
    'WebhookServiceImpl', 'SpaceServiceImpl', 'SyncLogServiceImpl',
}

SCOPE_CALL = re.compile(r'\bapply\w*Scope\s*\(|dataScopeService\s*\.\s*current\s*\(')
LIST_RETURN = re.compile(r'public\s+(PageResult|List)<')
DB_CALL = re.compile(r'\.selectPage\s*\(|\.selectList\s*\(')

API_PREFIX = ('page', 'list', 'search', 'query', 'records', 'history',
              'expiring', 'tree', 'children', 'subtree')

# 这些参数属于分页/范围本身，不算父级限定
NOT_PARENT = {'pageNum', 'pageSize', 'orgId', 'tenantId', 'houseId', 'personId',
              'spaceId', 'deviceId'}


def scan_methods(src):
    """返回 [(方法名, 行号, 签名, 方法体)]。"""
    out = []
    for m in re.finditer(r'\n\s{4}public\s+[^;{]*?\b(\w+)\s*\(', src):
        name = m.group(1)
        brace = src.find('{', m.end())
        if brace < 0:
            continue
        depth = 0
        i = brace
        while i < len(src):
            if src[i] == '{':
                depth += 1
            elif src[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        sig = src[m.start():brace].lstrip()
        out.append((name, src[:m.start()].count('\n') + 1, sig, src[brace:i + 1]))
    return out


def params_of(sig):
    inner = sig[sig.find('(') + 1:]
    inner = inner.rsplit(')', 1)[0]
    names = re.findall(r'(\w+)\s*(?=,|$)', inner)
    return [n for n in names if n]


def has_parent_scope(sig):
    for p in params_of(sig):
        if p in NOT_PARENT:
            continue
        if p.lower().endswith('id') and p.lower() not in ('id',):
            return True
    return False


def scan():
    findings, checked = [], 0
    for dirpath, _d, files in os.walk(BACKEND):
        if not dirpath.replace('\\', '/').endswith('service/impl'):
            continue
        for fn in files:
            if not fn.endswith('ServiceImpl.java'):
                continue
            cls = fn[:-5]
            if cls in IGNORE_CLASSES:
                continue
            path = os.path.join(dirpath, fn)
            src = open(path, encoding='utf-8', errors='replace').read()
            rel = os.path.relpath(path, ROOT).replace('\\', '/')
            for name, line, sig, body in scan_methods(src):
                if not name.startswith(API_PREFIX):
                    continue
                if not LIST_RETURN.search(sig):
                    continue
                if not DB_CALL.search(body):
                    continue
                checked += 1
                if SCOPE_CALL.search(body):
                    continue
                if has_parent_scope(sig):
                    continue
                if '// scope:ignore' in body:
                    continue
                findings.append('%s:%d  %s.%s' % (rel, line, cls, name))
    return checked, findings


def main():
    checked, findings = scan()
    print('=' * 62)
    print('数据范围扫描：检查 %d 个对外列表方法' % checked)
    if not findings:
        print('  ✔ 全部列表方法均带数据范围过滤')
        print('=' * 62)
        return 0
    print('  发现 %d 处疑似缺数据范围：' % len(findings))
    for f in findings:
        print('    ✗ ' + f)
    print('=' * 62)
    return 1


if __name__ == '__main__':
    sys.exit(main())
