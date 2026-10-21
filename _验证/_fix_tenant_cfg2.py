# -*- coding: utf-8 -*-
"""重写忽略表清单的尾部三行（逗号必须在注释之前）"""
import io

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\common\config\MybatisTenantConfig.java')
lines = io.open(P, encoding='utf-8').read().split('\n')

# 定位 '"bp_open_api"' 所在行
idx = None
for i, ln in enumerate(lines):
    if '"bp_open_api"' in ln:
        idx = i
        break
assert idx is not None, '未找到 bp_open_api'

# 找到该 Set.of(...) 的结束行（下一处包含 ");" 的行）
end = idx
while end < len(lines) and ');' not in lines[end]:
    end += 1

new_block = [
    '            "bp_open_api",          // 开放接口清单',
    '            // 调用日志按 appKey 归属，表本身无 tenant_id 列；',
    '            // 若不忽略，租户插件会给 INSERT 注入 tenant_id 导致写入失败',
    '            "bp_open_call_log"',
]
lines[idx:end] = new_block + [lines[end]]

io.open(P, 'w', encoding='utf-8').write('\n'.join(lines))
print('已重写尾部：第 %d~%d 行' % (idx + 1, idx + len(new_block)))
for i in range(idx - 1, idx + len(new_block) + 2):
    print('  %d: %s' % (i + 1, lines[i]))
