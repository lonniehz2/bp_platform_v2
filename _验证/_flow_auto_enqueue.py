# -*- coding: utf-8 -*-
"""申请终审通过 → 自动入轮候（复用 AllocationService.enterQueue）。

实现要点：
- 用 @Autowired(required=false) 字段注入 AllocationService，避免改动既有构造器（会影响单测）
- 在同一事务内调用；失败只记 warn，不阻断审批主流程
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
AP = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                  'biz', 'service', 'impl', 'ApplicationServiceImpl.java')

s = io.open(AP, encoding='utf-8').read()

# 1) 字段注入
if 'allocationService' not in s:
    anchor = '    /** 信用惩戒服务（可选注入，避免影响既有构造器与单测） */'
    inject = '''    /** 轮候服务（可选注入）：终审通过后自动入队 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.service.AllocationService allocationService;

'''
    if anchor in s:
        s = s.replace(anchor, inject + anchor, 1)
    else:
        i = s.find('    private final SnowflakeIdGenerator idGen;')
        j = s.find('\n', i) + 1
        s = s[:j] + inject + s[j:]

# 2) 通过后调用
if 'autoEnqueue(e)' not in s:
    s = s.replace('        transition(e, ApplicationStatus.APPROVED);',
                  '''        transition(e, ApplicationStatus.APPROVED);
        autoEnqueue(e);''', 1)

# 3) 辅助方法
if 'private void autoEnqueue' not in s:
    helper = '''
    /**
     * 终审通过后自动进入轮候库。
     *
     * <p>业务上「审核通过」的下一步就是排队等房，此前需要人工到轮候页入队，
     * 效率低且容易漏单。这里复用 AllocationService.enterQueue 在审批事务内完成入队；
     * 入队失败只记警告，不影响审批本身。
     */
    private void autoEnqueue(BizApplication app) {
        if (allocationService == null || app == null) {
            return;
        }
        try {
            com.yundao.bp.biz.dto.WaitingEnterCmd cmd = new com.yundao.bp.biz.dto.WaitingEnterCmd(
                    app.getId(), app.getSecurityType(), app.getOrgId(), java.math.BigDecimal.ZERO,
                    null);
            allocationService.enterQueue(cmd);
            log.info("申请 {} 审核通过，已自动进入轮候", app.getId());
        } catch (Exception ex) {
            log.warn("申请 {} 自动入轮候失败（不影响审批）：{}", app.getId(), ex.getMessage());
        }
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + helper + s[i:]

io.open(AP, 'w', encoding='utf-8', newline='').write(s)
print('已写入 autoEnqueue')
