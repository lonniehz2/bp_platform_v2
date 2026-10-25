# -*- coding: utf-8 -*-
"""组织机构：补「更新」「启用/停用」接口与服务实现。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
IAM = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iam')

# ---------- 1) 服务接口 ----------
P = os.path.join(IAM, 'service', 'OrgService.java')
s = io.open(P, encoding='utf-8').read()
if 'OrgVO update(' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 更新组织（名称/编码/地址/社区/排序/备注等）。 */
    OrgVO update(Long id, com.yundao.bp.iam.dto.OrgCreateCmd cmd);

    /** 启用 / 停用组织。 */
    OrgVO changeStatus(Long id, String status);
''' + s[i:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('OrgService：已加 update / changeStatus')

# ---------- 2) 服务实现 ----------
P = os.path.join(IAM, 'service', 'impl', 'OrgServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()
if 'public OrgVO update(' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    @Override
    @Transactional(rollbackFor = Exception.class)
    public OrgVO update(Long id, com.yundao.bp.iam.dto.OrgCreateCmd cmd) {
        IamOrg e = orgMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("组织");
        }
        if (cmd.orgName() != null && !cmd.orgName().isBlank()) {
            e.setOrgName(cmd.orgName());
        }
        if (cmd.orgCode() != null && !cmd.orgCode().isBlank()) {
            e.setOrgCode(cmd.orgCode());
        }
        if (cmd.parentId() != null) {
            if (id.equals(cmd.parentId())) {
                throw BizException.paramInvalid("上级组织不能是自己");
            }
            e.setParentId(cmd.parentId());
        }
        if (cmd.orgType() != null && !cmd.orgType().isBlank()) {
            e.setOrgType(cmd.orgType());
        }
        e.setProvince(cmd.province());
        e.setCity(cmd.city());
        e.setDistrict(cmd.district());
        e.setStreet(cmd.street());
        e.setCommunity(cmd.community());
        e.setAddress(cmd.address());
        if (cmd.sortNo() != null) {
            e.setSortNo(cmd.sortNo());
        }
        e.setRemark(cmd.remark());
        e.setUpdateTime(java.time.LocalDateTime.now());
        orgMapper.updateById(e);
        return OrgVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OrgVO changeStatus(Long id, String status) {
        IamOrg e = orgMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("组织");
        }
        if (!java.util.List.of("ENABLED", "DISABLED").contains(status)) {
            throw BizException.paramInvalid("状态只能是 ENABLED / DISABLED");
        }
        e.setStatus(status);
        e.setUpdateTime(java.time.LocalDateTime.now());
        orgMapper.updateById(e);
        return OrgVO.from(e);
    }
''' + s[i:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('OrgServiceImpl：已实现 update / changeStatus')

# ---------- 3) 控制器 ----------
P = os.path.join(IAM, 'controller', 'OrgController.java')
s = io.open(P, encoding='utf-8').read()
if 'PutMapping' not in s:
    s = s.replace('import org.springframework.web.bind.annotation.PostMapping;',
                  'import org.springframework.web.bind.annotation.PostMapping;\n'
                  'import org.springframework.web.bind.annotation.PutMapping;')
if '/{id}/status' not in s:
    block = '''
    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:update")
    @PutMapping("/{id}")
    public R<OrgVO> update(@PathVariable Long id, @Valid @RequestBody OrgCreateCmd cmd) {
        return R.ok(orgService.update(id, cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:update")
    @PostMapping("/{id}/status")
    public R<OrgVO> changeStatus(@PathVariable Long id, @RequestBody java.util.Map<String, String> body) {
        return R.ok(orgService.changeStatus(id, body == null ? null : body.get("status")));
    }
'''
    anchor = '''    @com.yundao.bp.iam.security.RequirePerm("orgs:orgs:delete")'''
    s = s.replace(anchor, block + '\n' + anchor, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('OrgController：已加 PUT /{id} 与 POST /{id}/status')
