# -*- coding: utf-8 -*-
"""把无 tenant_id 的表加入租户忽略清单（bp_open_call_log）"""
import io

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\common\config\MybatisTenantConfig.java')
s = io.open(P, encoding='utf-8').read()

if 'bp_open_call_log' in s:
    print('已在忽略表清单')
else:
    old = '"bp_open_api"           // 开放接口清单'
    assert old in s, '锚点缺失'
    s = s.replace(old,
                  old + '\n'
                  '            // 调用日志按 appKey 归属，表本身无 tenant_id 列，'
                  '若不过滤会因 INSERT 注入 tenant_id 而失败\n'
                  '            "bp_open_call_log"', 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已加入 bp_open_call_log')

# 同时检查是否还有无 tenant_id 却被拦截的表（快速核对：这些表已知无该列）
MAYBE = ['bp_open_call_log', 'bp_open_api', 'bp_iam_tenant', 'bp_iam_permission',
         'bp_sys_dict', 'bp_sys_config', 'bp_msg_template', 'bp_rpt_report_def',
         'bp_rpt_screen_def']
missing = [t for t in MAYBE if t not in s]
print('清单内仍缺：%s' % (missing if missing else '无'))
