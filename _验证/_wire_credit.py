# -*- coding: utf-8 -*-
"""把信用校验接入申请创建（让 5 年禁申真正生效）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
p = os.path.join(BASE, r'biz\service\impl\ApplicationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if 'creditService' in s:
    print('已接入，跳过')
    raise SystemExit

# 1) import + 可选注入
s = s.replace('import com.yundao.bp.biz.mapper.BizReviewRecordMapper;',
              'import com.yundao.bp.biz.mapper.BizReviewRecordMapper;\n'
              'import com.yundao.bp.biz.service.CreditService;', 1)

s = s.replace('''    private final BizApplicationMapper appMapper;
    private final BizReviewRecordMapper reviewMapper;
    private final SnowflakeIdGenerator idGen;''',
              '''    private final BizApplicationMapper appMapper;
    private final BizReviewRecordMapper reviewMapper;
    private final SnowflakeIdGenerator idGen;

    /** 信用惩戒服务（可选注入，避免影响既有构造器与单测） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private CreditService creditService;''', 1)

# 2) 在申请创建最前面加信用校验
old = '''    public ApplicationVO create(ApplicationCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        // 保障房必备：真实性承诺书 + 同意核实'''
new = '''    public ApplicationVO create(ApplicationCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        // ⭐ 信用惩戒校验（决策 D31）：处于限制申请期的人员不得申请
        // 放在最前面，避免"填完一堆材料才被告知不能申请"
        if (creditService != null) {
            creditService.checkApplyBan(cmd.personId());
        }

        // 保障房必备：真实性承诺书 + 同意核实'''
assert old in s, 'create 锚点缺失'
s = s.replace(old, new, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ 信用校验已接入申请创建（位于所有校验之前）')
