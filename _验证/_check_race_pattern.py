# -*- coding: utf-8 -*-
"""并发「先查后写」扫描（按资金风险分级）。

高风险（HIGH）：涉及金额增减的方法——退款、核销、发放、减免、抵扣、催缴。
  这类方法若「先查后写」且无保护，并发下会**重复入账/超额处理**，
  已实际发生两起：账单核销超收、押金退款超退。

中风险（MED）：状态流转类（授权、钥匙、工单、报送），并发可能重复流转。

低风险（LOW）：新建/更新类 CRUD，通常有唯一索引兜底，仅提示。

保护措施（任一即可豁免）：
  synchronized / ConcurrentHashMap 锁 / for update 行锁 /
  条件更新（UpdateWrapper、setSql）/ INSERT IGNORE / on duplicate key
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BACKEND = os.path.join(ROOT, 'backend', 'src', 'main', 'java')

READ = re.compile(r'\.(selectCount|selectOne|selectById|selectList)\s*\(')
WRITE = re.compile(r'\.(insert|updateById|update)\s*\(')
GUARD = re.compile(r'synchronized|lockForUpdate|for update|UpdateWrapper|setSql|'
                   r'computeIfAbsent|INSERT IGNORE|on duplicate key', re.I)

HIGH_HINTS = re.compile(r'refund|deposit|bill|payment|subsid|waive|offset|arrear|'
                        r'allocat|settle|reconcil', re.I)
MED_HINTS = re.compile(r'grant|keyring|order|report|inspection|adapter|rule|'
                       r'webhook|message|status', re.I)

IGNORE_CLASSES = {
    'SysRegionServiceImpl', 'SysDictServiceImpl', 'SysParamServiceImpl',
    'PermissionServiceImpl', 'RoleServiceImpl', 'MenuServiceImpl',
    'MetricServiceImpl', 'ScreenServiceImpl', 'ReportServiceImpl',
    'AuthServiceImpl', 'IamOrgServiceImpl', 'DictServiceImpl',
    'ConfigServiceImpl', 'AuditServiceImpl', 'FileServiceImpl',
    # 已确认有锁/条件更新保护的实现
    'BillingServiceImpl', 'DepositRefundServiceImpl',
}


def methods(src):
    out = []
    for m in re.finditer(r'\n\s{4}(?:public|private|protected)\s+[^;{]*?\b(\w+)\s*\(', src):
        name = m.group(1)
        brace = src.find('{', m.end())
        if brace < 0:
            continue
        depth, i = 0, brace
        while i < len(src):
            if src[i] == '{':
                depth += 1
            elif src[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        out.append((name, src[:m.start()].count('\n') + 1, src[brace:i + 1]))
    return out


def classify(rel, name, body):
    text = (rel + ' ' + name + ' ' + body)[:4000]
    if HIGH_HINTS.search(rel) or HIGH_HINTS.search(name):
        return 'HIGH'
    if MED_HINTS.search(name):
        return 'MED'
    return 'LOW'


def main():
    buckets = {'HIGH': [], 'MED': [], 'LOW': []}
    checked = 0
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
            for name, line, body in methods(src):
                if not (READ.search(body) and WRITE.search(body)):
                    continue
                checked += 1
                if GUARD.search(body):
                    continue
                if '// race:ignore' in body:
                    continue
                level = classify(rel, name, body)
                buckets[level].append('%s:%d  %s.%s'
                                      % (rel.replace('backend/src/main/java/com/yundao/bp/', ''),
                                         line, cls, name))

    print('=' * 72)
    print('先查后写扫描：检查 %d 个含读写的方法' % checked)
    for level, label in (('HIGH', '高风险（资金增减）'),
                         ('MED', '中风险（状态流转）'),
                         ('LOW', '低风险（CRUD 新建/更新）')):
        items = buckets[level]
        print('\n[%s] %s：%d 处' % (level, label, len(items)))
        for it in items[:12]:
            print('    ✗ ' + it)
        if len(items) > 12:
            print('    … 另有 %d 处' % (len(items) - 12))
    print('\n' + '=' * 72)
    if buckets['HIGH']:
        print('存在 %d 处高风险先查后写，需人工确认是否加锁/条件更新' % len(buckets['HIGH']))
        return 1
    print('  ✔ 无高风险先查后写')
    return 0


if __name__ == '__main__':
    sys.exit(main())
