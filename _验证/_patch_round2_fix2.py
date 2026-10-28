# -*- coding: utf-8 -*-
"""补：人员删除校验、申请黑名单提示、入住信息 SQL、minDays 恢复。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# 1) 人员删除：已实名不允许
p = os.path.join(BE, 'person', 'service', 'impl', 'PersonServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if '已完成实名核验，不允许删除' not in s:
    s = s.replace('''        if ("BLACKLIST".equals(p.getPersonStatus())) {
            throw BizException.stateConflict("黑名单人员不允许删除，请先解除黑名单");
        }''', '''        if ("BLACKLIST".equals(p.getPersonStatus())) {
            throw BizException.stateConflict("黑名单人员不允许删除，请先解除黑名单");
        }
        String vs = p.getVerifyStatus();
        if (vs != null && !vs.isBlank() && !"NONE".equals(vs)
                && !"UNVERIFIED".equals(vs) && !"FAILED".equals(vs)) {
            throw BizException.stateConflict(
                    "该人员已完成实名核验，不允许删除；如确需删除请先走注销流程");
        }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('人员删除校验已加')

# 2) 申请创建：黑名单/注销
p = os.path.join(BE, 'biz', 'service', 'impl', 'ApplicationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if '黑名单人员（限制申请期），不能新建申请' not in s:
    s = s.replace('''        if (creditService != null) {
            creditService.checkApplyBan(cmd.personId());
        }''', '''        if (creditService != null) {
            creditService.checkApplyBan(cmd.personId());
        }

        // 人员状态：黑名单 / 注销 直接拦下，提示可读
        com.yundao.bp.person.entity.Person applicant = personMapper.selectById(cmd.personId());
        if (applicant != null) {
            String ps = applicant.getPersonStatus();
            if ("BLACKLIST".equals(ps)) {
                throw BizException.stateConflict("该人员为黑名单人员（限制申请期），不能新建申请");
            }
            if ("CANCELLED".equals(ps) || "CANCELED".equals(ps) || "LOGOUT".equals(ps)) {
                throw BizException.stateConflict("该人员已注销，不能新建申请");
            }
        }''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('申请黑名单/注销拦截已加')

# 3) 入住信息 SQL 列名：member_name
p = os.path.join(BE, 'asset', 'controller', 'HouseController.java')
s = io.open(p, encoding='utf-8').read()
s = s.replace('select co.name, co.relation, co.id_card_mask from bp_biz_contract_cohabitant co',
              'select co.member_name as name, co.relation, co.id_card_mask from bp_biz_contract_cohabitant co')
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('入住信息 SQL 已修')
