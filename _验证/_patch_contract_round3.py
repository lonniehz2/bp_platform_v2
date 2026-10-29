# -*- coding: utf-8 -*-
"""合同：承租人信息回填、房源在租校验；批次房源允许已配租历史；变更生效延迟。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return s


# ---------- A. 合同创建：回填承租人信息 + 一房一租 ----------
p = os.path.join(BE, 'biz', 'service', 'impl', 'ContractServiceImpl.java')
patch(p, [
    ('''        Long activeContracts = mapper.selectCount(
                new LambdaQueryWrapper<BizContract>()
                        .eq(BizContract::getLesseePersonId, cmd.lesseePersonId())
                        .eq(BizContract::getHouseId, cmd.houseId())
                        .in(BizContract::getContractStatus,
                                "SIGNING", "EFFECTIVE", "RENEWING"));
        if (activeContracts != null && activeContracts > 0) {
            throw BizException.stateConflict("该承租人对该房源已有在签/在租合同，不能重复签约");
        }''',
     '''        // 一房一租：该房源已有在制/在租合同即拒绝
        Long houseActive = mapper.selectCount(
                new LambdaQueryWrapper<BizContract>()
                        .eq(BizContract::getHouseId, cmd.houseId())
                        .in(BizContract::getContractStatus,
                                "DRAFT", "SIGNING", "EFFECTIVE", "RENEWING"));
        if (houseActive != null && houseActive > 0) {
            throw BizException.stateConflict("该房源已有履约中/签约中的合同，不能重复签约");
        }''', '一房一租校验'),
    ('''        e.setLesseePersonId(cmd.lesseePersonId());
        e.setLesseeName(cmd.lesseeName());
        e.setLesseePhone(cmd.lesseePhone());
        e.setLesseeIdCardMask(cmd.lesseeIdCardMask());''',
     '''        e.setLesseePersonId(cmd.lesseePersonId());
        // 姓名/手机/证件：前端未传时按人员档案补齐，避免保存后为空
        String lesseeName = blankToNull(cmd.lesseeName());
        String lesseePhone = blankToNull(cmd.lesseePhone());
        String lesseeIdCard = blankToNull(cmd.lesseeIdCardMask());
        if (lesseeName == null || lesseePhone == null || lesseeIdCard == null) {
            com.yundao.bp.person.entity.Person person =
                    personMapper == null ? null : personMapper.selectById(cmd.lesseePersonId());
            if (person != null) {
                if (lesseeName == null) {
                    lesseeName = blankToNull(person.getPersonName()) != null
                            ? person.getPersonName() : person.getRealName();
                }
                if (lesseePhone == null) {
                    lesseePhone = person.getPhone();
                }
                if (lesseeIdCard == null) {
                    lesseeIdCard = person.getIdCardMask();
                }
            }
        }
        e.setLesseeName(lesseeName);
        e.setLesseePhone(lesseePhone);
        e.setLesseeIdCardMask(lesseeIdCard);''', '承租人信息回填'),
])

# ---------- B. 批次房源：允许历史已配租批次 ----------
p = os.path.join(BE, 'biz', 'service', 'impl', 'AllocationServiceImpl.java')
patch(p, [
    ('''                BatchStatus obs = batchStatusOf(ob);
                if (!obs.isTerminal()) {
                    throw BizException.stateConflict("房源「" + (h.getHouseName() == null
                            ? h.getHouseCode() : h.getHouseName())
                            + "」已在批次 " + ob.getBatchNo() + "（" + obs.label() + "）中，不能重复入池");
                }''',
     '''                BatchStatus obs = batchStatusOf(ob);
                // 已配租（ALLOCATED）属于历史，退房后可再次入池；只拦仍在报名/摇号/选房阶段的批次
                boolean activePool = obs == BatchStatus.DRAFT || obs == BatchStatus.PUBLISHED
                        || obs == BatchStatus.SIGNUP || obs == BatchStatus.LOTTERY
                        || obs == BatchStatus.LOTTERY_DONE || obs == BatchStatus.SELECTING;
                if (activePool) {
                    throw BizException.stateConflict("房源「" + (h.getHouseName() == null
                            ? h.getHouseCode() : h.getHouseName())
                            + "」已在批次 " + ob.getBatchNo() + "（" + obs.label() + "）中，不能重复入池");
                }''', '批次房源历史放行'),
])

# personMapper 是否存在
s = io.open(p, encoding='utf-8').read()
if 'PersonMapper personMapper' not in io.open(
        os.path.join(BE, 'biz', 'service', 'impl', 'ContractServiceImpl.java'),
        encoding='utf-8').read():
    print('  ! ContractServiceImpl 无 personMapper 字段，需补充')
