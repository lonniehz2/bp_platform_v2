# -*- coding: utf-8 -*-
"""计费规则：补 PUT（编辑）与 DELETE（删除）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

# ---------- 接口 ----------
P = os.path.join(BK, 'service', 'FeeItemService.java')
s = io.open(P, encoding='utf-8').read()
if 'FinBillingRule updateRule(' not in s:
    s = s.replace('    FinBillingRule createRule(BillingRuleCreateCmd cmd);',
'''    FinBillingRule createRule(BillingRuleCreateCmd cmd);

    /** 编辑计费规则；已审批通过的规则不允许改动（须新建）。 */
    FinBillingRule updateRule(Long id, BillingRuleCreateCmd cmd);

    /** 删除（逻辑删）计费规则；已审批通过的规则不可删。 */
    void deleteRule(Long id);''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('FeeItemService 已加 updateRule/deleteRule')

# ---------- 实现 ----------
P = os.path.join(BK, 'service', 'impl', 'FeeItemServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()
if 'public FinBillingRule updateRule(' not in s:
    impl = '''
    @Override
    @Transactional(rollbackFor = Exception.class)
    public FinBillingRule updateRule(Long id, BillingRuleCreateCmd cmd) {
        FinBillingRule e = requireRule(id);
        if ("APPROVED".equals(e.getApproveStatus())) {
            throw BizException.stateConflict("已审批通过的规则不可修改，请新建规则后再审批");
        }
        if (cmd.feeItemId() != null && !cmd.feeItemId().equals(e.getFeeItemId())) {
            FinFeeItem item = feeItemMapper.selectById(cmd.feeItemId());
            if (item == null) {
                throw BizException.notFound("收费项目");
            }
            e.setFeeItemId(cmd.feeItemId());
        }
        if (cmd.effectiveStart() != null && cmd.effectiveEnd() != null
                && !cmd.effectiveEnd().isAfter(cmd.effectiveStart())) {
            throw BizException.paramInvalid("生效结束日必须晚于开始日");
        }
        if (cmd.ruleCode() != null && !cmd.ruleCode().isBlank()) {
            e.setRuleCode(cmd.ruleCode());
        }
        if (cmd.ruleName() != null && !cmd.ruleName().isBlank()) {
            e.setRuleName(cmd.ruleName());
        }
        e.setOrgId(cmd.orgId());
        e.setHouseType(cmd.houseType());
        e.setSecurityType(cmd.securityType());
        e.setIncomeLevel(cmd.incomeLevel());
        if (cmd.ruleType() != null && !cmd.ruleType().isBlank()) {
            e.setRuleType(cmd.ruleType());
        }
        e.setPriceConfig(cmd.priceConfig());
        if (cmd.effectiveStart() != null) {
            e.setEffectiveStart(cmd.effectiveStart());
        }
        e.setEffectiveEnd(cmd.effectiveEnd());
        if (cmd.priority() != null) {
            e.setPriority(cmd.priority());
        }
        e.setUpdateTime(LocalDateTime.now());
        ruleMapper.updateById(e);
        return e;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteRule(Long id) {
        FinBillingRule e = requireRule(id);
        if ("APPROVED".equals(e.getApproveStatus())) {
            throw BizException.stateConflict("已审批通过的规则不可删除，可改为停用");
        }
        ruleMapper.deleteById(id);
    }

    private FinBillingRule requireRule(Long id) {
        FinBillingRule e = ruleMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("计费规则");
        }
        return e;
    }

'''
    anchor = '    @Override\n    public FinBillingRule getRule('
    if anchor in s:
        s = s.replace(anchor, impl + anchor, 1)
    else:
        # 退化：插到 approveRule 之前
        s = s.replace('    @Override\n    @Transactional(rollbackFor = Exception.class)\n    public FinBillingRule approveRule(',
                      impl + '    @Override\n    @Transactional(rollbackFor = Exception.class)\n    public FinBillingRule approveRule(', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('FeeItemServiceImpl 已加 updateRule/deleteRule')

# ---------- 控制器 ----------
P = os.path.join(BK, 'controller', 'FeeItemController.java')
s = io.open(P, encoding='utf-8').read()
if 'PutMapping("/billing-rules/{id}")' not in s:
    s = s.replace('''    /** 政府限价审批。 */''',
'''    /** 编辑计费规则（已审批通过的不可改）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:billing-rules:create")
    @org.springframework.web.bind.annotation.PutMapping("/billing-rules/{id}")
    public R<FinBillingRule> updateRule(@PathVariable Long id,
                                        @Valid @RequestBody BillingRuleCreateCmd cmd) {
        return R.ok(service.updateRule(id, cmd));
    }

    /** 删除计费规则（已审批通过的不可删）。 */
    @com.yundao.bp.iam.security.RequirePerm("fin:billing-rules:create")
    @org.springframework.web.bind.annotation.DeleteMapping("/billing-rules/{id}")
    public R<Void> deleteRule(@PathVariable Long id) {
        service.deleteRule(id);
        return R.ok(null);
    }

    /** 政府限价审批。 */''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('FeeItemController 已加 PUT/DELETE billing-rules')
