# -*- coding: utf-8 -*-
"""三件事：
1) 快捷签约补全承租人姓名/手机/脱敏证件（查人员表）
2) 公示关联批次：bp_biz_publicity 增加 batch_id
3) 新增 GET /publicities/{id}/winners（中签名单，身份证脱敏）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
B = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')

# ---------- 1) 快捷签约：补全承租人信息 ----------
I = os.path.join(B, 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(I, encoding='utf-8').read()

if 'quickSignPersonMapper' not in s:
    inject = '''
    /** 人员查询（快捷签约补全承租人姓名与脱敏证件） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonMapper quickSignPersonMapper;
'''
    j = s.find('    public ContractServiceImpl(')
    s = s[:j] + inject + '\n' + s[j:]

old_block = '''                        null,                   // lesseeName（服务端按人员补齐）
                        null,                   // lesseePhone
                        null,                   // lesseeIdCardMask'''
new_block = '''                        lesseeName,             // lesseeName（按人员补齐）
                        lesseePhone,            // lesseePhone
                        lesseeIdCardMask,       // lesseeIdCardMask（脱敏）'''
if old_block in s:
    s = s.replace(old_block, new_block, 1)

# 在创建合同前查询人员
anchor = '        // 2) 创建合同草稿（金额口径：actualPay 由服务端计算）'
if 'lesseeName =' not in s:
    person_lookup = '''        // 2) 查人员补齐承租人信息（合同文本需要姓名与脱敏证件）
        String lesseeName = null;
        String lesseePhone = null;
        String lesseeIdCardMask = null;
        if (quickSignPersonMapper != null) {
            com.yundao.bp.person.entity.Person person =
                    quickSignPersonMapper.selectById(cmd.personId());
            if (person != null) {
                lesseeName = person.getRealName();
                lesseePhone = person.getPhone();
                lesseeIdCardMask = person.getIdCardMask();
            }
        }

'''
    s = s.replace(anchor, person_lookup + anchor.replace('// 2)', '// 3)'), 1)

io.open(I, 'w', encoding='utf-8', newline='').write(s)
print('ContractServiceImpl：已补全承租人信息')

# ---------- 2) 公示实体加 batchId ----------
E = os.path.join(B, 'entity', 'BizPublicity.java')
s = io.open(E, encoding='utf-8').read()
if 'batchId' not in s:
    s = s.replace('    private Long orgId;',
                  '    private Long orgId;\n\n'
                  '    /** 关联配租批次（公示中签名单用，可为空） */\n'
                  '    private Long batchId;', 1)
    io.open(E, 'w', encoding='utf-8', newline='').write(s)
    print('BizPublicity：已加 batchId')

# ---------- 3) 公示 Cmd / VO 加 batchId ----------
C = os.path.join(B, 'dto', 'PublicityCreateCmd.java')
s = io.open(C, encoding='utf-8').read()
if 'batchId' not in s:
    s = s.replace('        Long orgId,', '        Long orgId,\n\n        /** 关联配租批次（可选，用于公示中签名单） */\n        Long batchId,', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('PublicityCreateCmd：已加 batchId')

V = os.path.join(B, 'dto', 'PublicityVO.java')
s = io.open(V, encoding='utf-8').read()
if 'batchId' not in s:
    s = s.replace('        Long orgId,', '        Long orgId,\n        Long batchId,', 1)
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('PublicityVO：已加 batchId')

# ---------- 4) 中签名单 VO ----------
W = os.path.join(B, 'dto', 'PublicityWinnerVO.java')
io.open(W, 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.biz.dto;

/**
 * 公示中签名单中的一条记录。
 *
 * @param personName     中签人姓名
 * @param idCardMask     脱敏身份证号
 * @param phoneMask      脱敏手机号
 * @param houseName      中签房源
 * @param lotterySeq     摇号序号
 * @param selectSeq      选房序号
 * @param resultTypeLabel 结果（中签/候补等）
 */
public record PublicityWinnerVO(
        Long personId,
        String personName,
        String idCardMask,
        String phoneMask,
        String houseName,
        String lotterySeq,
        Integer selectSeq,
        String resultType,
        String resultTypeLabel
) {
}
''', )
print('PublicityWinnerVO：已创建')
