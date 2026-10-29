# -*- coding: utf-8 -*-
"""MeVO 增加租户名/组织名，供页头展示。"""
import io

# 1) MeVO
p = r'..\backend\src\main\java\com\yundao\bp\iam\dto\MeVO.java'
s = io.open(p, encoding='utf-8').read()
if 'tenantName' not in s:
    s = s.replace('''        Long orgId,''', '''        Long orgId,
        String tenantName,
        String orgName,''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('MeVO updated')

# 2) AuthServiceImpl
p = r'..\backend\src\main\java\com\yundao\bp\iam\service\impl\AuthServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
if 'IamTenantMapper' not in s:
    s = s.replace('''    private final SnowflakeIdGenerator idGen;''',
                  '''    private final SnowflakeIdGenerator idGen;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamTenantMapper tenantMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamOrgMapper orgMapper;''', 1)
    s = s.replace('''        return new MeVO(user.getId(), user.getUsername(), user.getRealName(),
                user.getTenantId(), user.getOrgId(), user.getUserType(), admin,
                new ArrayList<>(perms), roleIds);''',
                  '''        String tenantName = null;
        if (tenantMapper != null && user.getTenantId() != null) {
            com.yundao.bp.iam.entity.IamTenant t = tenantMapper.selectById(user.getTenantId());
            if (t != null) {
                tenantName = t.getTenantName();
            }
        }
        String orgName = null;
        if (user.getOrgId() == null) {
            orgName = "平台";
        } else if (orgMapper != null) {
            com.yundao.bp.iam.entity.IamOrg o = orgMapper.selectById(user.getOrgId());
            if (o != null) {
                orgName = o.getOrgName();
            }
        }
        return new MeVO(user.getId(), user.getUsername(), user.getRealName(),
                user.getTenantId(), user.getOrgId(), tenantName,
                orgName == null ? "平台" : orgName, user.getUserType(), admin,
                new ArrayList<>(perms), roleIds);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('AuthServiceImpl updated')
