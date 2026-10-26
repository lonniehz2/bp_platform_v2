# -*- coding: utf-8 -*-
"""两项后端增强：
  1) 规则可编辑：PUT /rules/rules/{id}（仅草稿规则集可改）
  2) 菜单角标区分「设备告警(DevEvent)」与「告警处理(OpsAlert)」
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- 1) Service 接口 ----------
P = os.path.join(BK, 'rule', 'service', 'RuleEngineService.java')
s = io.open(P, encoding='utf-8').read()
if 'RuleRule updateRule(' not in s:
    s = s.replace('    RuleRule addRule(',
                  '''    /** 修改规则（仅未发布的规则集可改）。 */
    RuleRule updateRule(Long ruleId, String code, String name, String conditionExpr,
                        String thresholdJson, String severity, String actionsJson,
                        Integer priority);

    RuleRule addRule(''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('RuleEngineService 已加 updateRule')

# ---------- 2) Service 实现 ----------
P = os.path.join(BK, 'rule', 'service', 'impl', 'RuleEngineServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()
if 'public RuleRule updateRule(' not in s:
    impl = '''
    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public RuleRule updateRule(Long ruleId, String code, String name, String conditionExpr,
                               String thresholdJson, String severity, String actionsJson,
                               Integer priority) {
        RuleRule r = ruleMapper.selectById(ruleId);
        if (r == null) {
            throw BizException.notFound("规则");
        }
        RuleRuleset rs = requireRuleset(r.getRulesetId());
        if ("PUBLISHED".equals(rs.getRulesetStatus())) {
            throw BizException.stateConflict("已发布的规则集不可直接改规则，请新建版本");
        }
        if (code != null && !code.isBlank() && !code.equals(r.getRuleCode())) {
            Long dup = ruleMapper.selectCount(new LambdaQueryWrapper<RuleRule>()
                    .eq(RuleRule::getRulesetId, r.getRulesetId())
                    .eq(RuleRule::getRuleCode, code));
            if (dup != null && dup > 0) {
                throw new BizException(ErrorCode.DUPLICATED,
                        "该规则集内已存在规则编码：" + code);
            }
            r.setRuleCode(code);
        }
        try {
            if (thresholdJson != null && !thresholdJson.isBlank()) {
                JSON.readTree(thresholdJson);
            }
        } catch (Exception e) {
            throw BizException.paramInvalid("阈值配置不是合法 JSON：" + e.getMessage());
        }
        if (name != null && !name.isBlank()) {
            r.setRuleName(name);
        }
        r.setConditionExpr(conditionExpr);
        r.setThresholdJson(thresholdJson);
        if (severity != null && !severity.isBlank()) {
            r.setSeverity(severity);
        }
        r.setActionsJson(actionsJson);
        if (priority != null) {
            r.setPriority(priority);
        }
        r.setUpdateTime(LocalDateTime.now());
        ruleMapper.updateById(r);
        return r;
    }

'''
    if 'public RuleRule setRuleStatus(' in s:
        s = s.replace('    @Override\n    public RuleRule setRuleStatus(',
                      impl + '    @Override\n    public RuleRule setRuleStatus(', 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('RuleEngineServiceImpl 已加 updateRule')

# ---------- 3) Controller ----------
P = os.path.join(BK, 'rule', 'controller', 'RuleEngineController.java')
s = io.open(P, encoding='utf-8').read()
if 'PutMapping("/rules/{id}")' not in s:
    s = s.replace('''    @PostMapping("/rules/{id}/status")''',
'''    /** 修改规则（仅草稿规则集可改）。 */
    @org.springframework.web.bind.annotation.PutMapping("/rules/{id}")
    @RequirePerm("rule:ruleset:manage")
    @Audit(type = "CONFIG", level = "IMPORTANT", action = "修改规则")
    public R<RuleRule> updateRule(@PathVariable Long id, @RequestBody RuleCmd cmd) {
        return R.ok(service.updateRule(id, cmd.code(), cmd.name(), cmd.conditionExpr(),
                cmd.thresholdJson(), cmd.severity(), cmd.actionsJson(), cmd.priority()));
    }

    @PostMapping("/rules/{id}/status")''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('RuleEngineController 已加 PUT /rules/{id}')

# ---------- 4) 菜单角标：设备告警单独计数 ----------
P = os.path.join(BK, 'iam', 'controller', 'MenuBadgeController.java')
s = io.open(P, encoding='utf-8', errors='replace').read()
if 'devAlerts' not in s:
    s = s.replace('''        out.put("pendingWorkOrders", countPendingWorkOrders());''',
'''        out.put("pendingWorkOrders", countPendingWorkOrders());
        // 设备告警（IoT 事件）与「告警处理」（平台告警单）是两套数据，分开计数
        out.put("devAlerts", countDevAlerts());''', 1)
    s = s.replace('''    private long countPendingWorkOrders() {''',
'''    /** 设备告警：未处理的告警类 IoT 事件（与设备告警页「未处理」一致）。 */
    private long countDevAlerts() {
        try {
            java.util.List<String> alarms = new java.util.ArrayList<>();
            for (com.yundao.bp.dev.constant.DevEventType t
                    : com.yundao.bp.dev.constant.DevEventType.values()) {
                if (t.alarm()) {
                    alarms.add(t.name());
                }
            }
            Long n = devEventMapper.selectCount(
                    new LambdaQueryWrapper<com.yundao.bp.dev.entity.DevEvent>()
                            .in(com.yundao.bp.dev.entity.DevEvent::getIdentifier, alarms)
                            .eq(com.yundao.bp.dev.entity.DevEvent::getHandled, 0));
            return n == null ? 0 : n;
        } catch (Exception e) {
            return 0;
        }
    }

    private long countPendingWorkOrders() {''', 1)
    # 注入 mapper
    if 'devEventMapper' not in s.split('public MenuBadgeController')[0]:
        s = s.replace('    private final OpsWorkorderMapper workOrderMapper;',
                      '    private final OpsWorkorderMapper workOrderMapper;\n'
                      '    private final com.yundao.bp.dev.mapper.DevEventMapper devEventMapper;', 1)
        s = s.replace('''                               OpsWorkorderMapper workOrderMapper) {''',
'''                               OpsWorkorderMapper workOrderMapper,
                               com.yundao.bp.dev.mapper.DevEventMapper devEventMapper) {''', 1)
        s = s.replace('''        this.workOrderMapper = workOrderMapper;''',
'''        this.workOrderMapper = workOrderMapper;
        this.devEventMapper = devEventMapper;''', 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('MenuBadgeController 已加 devAlerts')
