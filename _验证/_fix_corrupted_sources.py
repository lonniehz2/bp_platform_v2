# -*- coding: utf-8 -*-
"""修复两处源码损坏（乱码 + 行粘连），并消除多余 @Override。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BIZ = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz',
                   'service', 'impl')

# ---------- 1) AllocationServiceImpl：去掉悬空 @Override + 修正注释 ----------
p = os.path.join(BIZ, 'AllocationServiceImpl.java')
s = io.open(p, encoding='utf-8', errors='replace').read()
s = s.replace('    @Override\n\n    /** ', '    /** ')
lines = s.splitlines()
out = []
for ln in lines:
    if 'DataScopeService dataScopeService' in ln or 'applyWaitingScope' in ln \
            or 'applyWaitingScope(qw)' in ln:
        pass
    if '/*' in ln and 'DataScopeService' in ln:
        pass
    out.append(ln)
s = '\n'.join(out) + '\n'
# 把带乱码的注释行替换为正确中文（按特征定位）
s = re.sub(r'    /\*\*[^\n]*ALL/ORG_SUB', '    /** 数据范围（ALL/ORG_SUB', s)
s = re.sub(r'    /\*\*[^\n]*BizWaitingQueue[^\n]*\*/\n',
           '    /** 轮候队列按人员维度限权：实体无 org 列，ORG 档不额外限制。 */\n', s)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('AllocationServiceImpl 已修复')

# ---------- 2) TerminationServiceImpl：补引号 + 拆开粘连行 ----------
q = os.path.join(BIZ, 'TerminationServiceImpl.java')
t = io.open(q, encoding='utf-8', errors='replace').read()
t = re.sub(r'throw BizException\.stateConflict\("[^"]*\);\n',
           'throw BizException.stateConflict("该合同已有进行中的退租单，不能重复申请");\n', t)
t = re.sub(r'(\s*)//[^\n]*过滤(\s*)if \(contractOrgIdMapper != null\) \{',
           r'\1// 组织取自合同，供数据范围过滤\n\1if (contractOrgIdMapper != null) {', t)
io.open(q, 'w', encoding='utf-8', newline='').write(t)
print('TerminationServiceImpl 已修复')
