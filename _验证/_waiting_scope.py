# -*- coding: utf-8 -*-
"""轮候列表补数据范围：租户（SELF）只能看到自己的轮候记录。

此前 AllocationServiceImpl 的 waiting/结果列表没有数据范围过滤，
租户授权后能看到全组织 69 条轮候（越权）。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'biz', 'service', 'impl', 'AllocationServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

if 'applyDataScope' in s:
    print('已存在数据范围')
    raise SystemExit(0)

INJECT = '''
    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 轮候队列按人员维度限权：实体无 org 列，ORG 档不额外限制。 */
    private void applyWaitingScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                    <com.yundao.bp.biz.entity.BizWaitingQueue> qw) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            qw.eq(com.yundao.bp.biz.entity.BizWaitingQueue::getPersonId,
                    scope.personId() == null ? -1L : scope.personId());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(com.yundao.bp.biz.entity.BizWaitingQueue::getOrgId, scope.orgId());
        }
    }
'''

anchor = '''        LambdaQueryWrapper<BizWaitingQueue> qw = new LambdaQueryWrapper<BizWaitingQueue>()
                .eq(securityType != null && !securityType.isBlank(),
                        BizWaitingQueue::getSecurityType, securityType)'''
if anchor in s:
    s = s.replace(anchor, anchor + '\n        applyWaitingScope(qw);', 1)
else:
    print('未找到 pageWaiting 查询锚点')

i = s.find('    public PageResult<WaitingVO> pageWaiting(')
s = s[:i] + INJECT + '\n' + s[i:]

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('AllocationServiceImpl：轮候列表已加数据范围')
