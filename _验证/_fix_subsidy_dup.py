# -*- coding: utf-8 -*-
"""补贴发放：并发下用唯一键兜底（给 insert 加 DuplicateKey 捕获）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'fin', 'service', 'impl', 'SubsidyServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

if 'DuplicateKeyException' in s:
    print('已有兜底')
    raise SystemExit(0)

TARGET = '        recordMapper.insert(e);'
TRY = (
    '        try {\n'
    '            recordMapper.insert(e);\n'
    '        } catch (org.springframework.dao.DuplicateKeyException dupEx) {\n'
    '            // 唯一索引 uk_contract_period 兜底：并发下同合同同期间只允许一条\n'
    '            throw BizException.stateConflict(\n'
    '                    "该合同 " + cmd.subsidyPeriod() + " 补贴已发放（并发幂等拒绝）");\n'
    '        }'
)

idx = s.find('public SubsidyRecordVO grant(')
if idx < 0:
    print('未找到 grant 方法')
    raise SystemExit(1)

seg = s[idx:idx + 6000]
if TARGET not in seg:
    print('grant 内未找到 insert 语句')
    raise SystemExit(1)

seg = seg.replace(TARGET, TRY, 1)
s = s[:idx] + seg + s[idx + 6000:]
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已在 grant 中加唯一键兜底')
