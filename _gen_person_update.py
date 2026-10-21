# -*- coding: utf-8 -*-
"""后端补人员编辑接口（PUT /persons/{id}）"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'


def find(name):
    for root, _, fs in os.walk(J):
        if name in fs:
            return os.path.join(root, name)
    return None


# ---------- 1) 新建 PersonUpdateCmd ----------
CMD = '''package com.yundao.bp.person.dto;

import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 人员信息修改入参。
 *
 * <p>不含身份证号：证件号是人员唯一标识的关键字段，修改需走专门流程，
 * 避免误改导致历史业务数据对不上。</p>
 */
public record PersonUpdateCmd(
        @Size(max = 64, message = "姓名不能超过 64 字符")
        String personName,
        @Size(max = 20, message = "手机号格式不正确")
        String phone,
        Long orgId,
        @Pattern(regexp = "^$|URBAN|RURAL|OTHER", message = "户籍类型不合法")
        String householdType,
        @Pattern(regexp = "^$|SINGLE|MARRIED|DIVORCED|WIDOWED", message = "婚姻状况不合法")
        String maritalStatus,
        @Size(max = 30, message = "学历不能超过 30 字符")
        String education,
        @Size(max = 128, message = "工作单位不能超过 128 字符")
        String employer,
        @Size(max = 500, message = "备注不能超过 500 字符")
        String remark) {
}
'''
dto_dir = os.path.join(J, 'person', 'dto')
os.makedirs(dto_dir, exist_ok=True)
io.open(os.path.join(dto_dir, 'PersonUpdateCmd.java'), 'w', encoding='utf-8').write(CMD)
print('  ✓ 新建 PersonUpdateCmd')

# ---------- 2) Service 接口 ----------
SP = find('PersonService.java')
s = io.open(SP, encoding='utf-8').read()
if 'update' not in s:
    s = s.replace('    PersonVO changeStatus(Long id, String targetStatus);',
                  '    /** 修改人员基本信息（不含身份证号） */\n'
                  '    PersonVO update(Long id, com.yundao.bp.person.dto.PersonUpdateCmd cmd);\n\n'
                  '    PersonVO changeStatus(Long id, String targetStatus);', 1)
    io.open(SP, 'w', encoding='utf-8').write(s)
    print('  ✓ PersonService 增加 update')

# ---------- 3) Service 实现 ----------
IP = find('PersonServiceImpl.java')
t = io.open(IP, encoding='utf-8').read()
if 'public PersonVO update(' not in t:
    m = re.search(r'(    @Override\s*\n)?    public PersonVO changeStatus\(', t)
    impl = '''    @Override
    public PersonVO update(Long id, com.yundao.bp.person.dto.PersonUpdateCmd cmd) {
        if (id == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("人员ID不能为空");
        }
        Person e = personMapper.selectById(id);
        if (e == null) {
            throw com.yundao.bp.common.exception.BizException.notFound("人员");
        }
        // 只覆盖非空字段：前端未传的不清空，避免误删已有信息
        if (cmd.personName() != null && !cmd.personName().isBlank()) {
            e.setPersonName(cmd.personName());
        }
        if (cmd.phone() != null && !cmd.phone().isBlank()) {
            e.setPhone(cmd.phone());
        }
        if (cmd.orgId() != null) {
            e.setOrgId(cmd.orgId());
        }
        if (cmd.householdType() != null && !cmd.householdType().isBlank()) {
            e.setHouseholdType(cmd.householdType());
        }
        if (cmd.maritalStatus() != null && !cmd.maritalStatus().isBlank()) {
            e.setMaritalStatus(cmd.maritalStatus());
        }
        if (cmd.education() != null && !cmd.education().isBlank()) {
            e.setEducation(cmd.education());
        }
        if (cmd.employer() != null && !cmd.employer().isBlank()) {
            e.setEmployer(cmd.employer());
        }
        if (cmd.remark() != null) {
            e.setRemark(cmd.remark());
        }
        personMapper.updateById(e);
        return PersonVO.from(e);
    }

'''
    if m:
        t = t[:m.start()] + impl + t[m.start():]
    else:
        # 退化：插到类末尾前
        idx = t.rfind('}')
        t = t[:idx] + impl + t[idx:]
    io.open(IP, 'w', encoding='utf-8').write(t)
    print('  ✓ PersonServiceImpl 增加 update 实现')

# ---------- 4) Controller ----------
CP = find('PersonController.java')
c = io.open(CP, encoding='utf-8').read()
if '/{id}"' not in c or 'PutMapping' not in c:
    m = re.search(r'    @PostMapping\("/\{id\}/status"\)', c)
    add = '''    @PutMapping("/{id}")
    public R<PersonVO> update(@PathVariable Long id,
                              @Valid @RequestBody com.yundao.bp.person.dto.PersonUpdateCmd cmd) {
        return R.ok(personService.update(id, cmd));
    }

'''
    if m:
        c = c[:m.start()] + add + c[m.start():]
    else:
        idx = c.rfind('}')
        c = c[:idx] + add + c[idx:]
    if 'PutMapping' not in c.split('public class')[0]:
        c = c.replace('import org.springframework.web.bind.annotation.PostMapping;',
                      'import org.springframework.web.bind.annotation.PostMapping;\n'
                      'import org.springframework.web.bind.annotation.PutMapping;', 1)
    io.open(CP, 'w', encoding='utf-8').write(c)
    print('  ✓ PersonController 增加 PUT /{id}')
