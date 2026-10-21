# -*- coding: utf-8 -*-
"""批量出账：批次级参数快速失败（期间校验前置）"""
import io

p = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\fin\service\impl\BillGenerationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if '批次级参数前置校验' in s:
    print('已修正过，跳过')
    raise SystemExit

old = '''    public GenerateBatchVO generateBatch(GenerateBatchCmd cmd) {
        boolean dryRun = cmd.dryRun() != null && cmd.dryRun();'''
new = '''    public GenerateBatchVO generateBatch(GenerateBatchCmd cmd) {
        // 批次级参数前置校验：期间、组织等属于整个批次共用的输入，
        // 无效时应当让整批直接失败（而不是逐项目返回 FAILED），便于调用方快速发现
        if (cmd.periodEnd().isBefore(cmd.periodStart())) {
            throw BizException.paramInvalid("费用截止日不能早于起始日");
        }
        boolean dryRun = cmd.dryRun() != null && cmd.dryRun();'''

assert old in s, 'anchor missing'
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('已加批次级期间校验')
