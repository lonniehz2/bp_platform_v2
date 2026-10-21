# -*- coding: utf-8 -*-
"""组织筛选「含下级」：人员分页支持 includeChildren。

后端：/persons 增加 includeChildren 参数；为 true 时按 org_path 前缀取整棵子树。
前端：组织下拉旁加「含下级」勾选项，并把它带进请求。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def patch(path, pairs, label):
    s = io.open(path, encoding='utf-8').read()
    hit = 0
    for a, b in pairs:
        if a in s:
            s = s.replace(a, b, 1)
            hit += 1
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    print('%s：%d/%d' % (label, hit, len(pairs)))


# ---------- 1. 服务接口 ----------
patch(os.path.join(J, 'person', 'service', 'PersonService.java'), [
    ('Long orgId, String personStatus);', 'Long orgId, String personStatus, Boolean includeChildren);'),
], 'PersonService 接口')

# ---------- 2. 控制器 ----------
cp = os.path.join(J, 'person', 'controller', 'PersonController.java')
s = io.open(cp, encoding='utf-8').read()
if 'includeChildren' not in s:
    s = s.replace('@RequestParam(required = false) String personStatus',
                  '''@RequestParam(required = false) String personStatus,
            @RequestParam(required = false) Boolean includeChildren''', 1)
    s = s.replace('service.page(pageNum, pageSize, keyword, orgId, personStatus)',
                  'service.page(pageNum, pageSize, keyword, orgId, personStatus, includeChildren)')
    io.open(cp, 'w', encoding='utf-8', newline='').write(s)
    print('PersonController：已加 includeChildren')

# ---------- 3. 服务实现 ----------
ip = os.path.join(J, 'person', 'service', 'impl', 'PersonServiceImpl.java')
s = io.open(ip, encoding='utf-8').read()
if 'includeChildren' not in s:
    s = s.replace('''                                     Long orgId, String personStatus) {''',
                  '''                                     Long orgId, String personStatus,
                                     Boolean includeChildren) {''', 1)
    s = s.replace('''        LambdaQueryWrapper<Person> qw = new LambdaQueryWrapper<Person>()
                .eq(orgId != null, Person::getOrgId, orgId)''',
                  '''        LambdaQueryWrapper<Person> qw = new LambdaQueryWrapper<Person>()
                .eq(orgId != null && !Boolean.TRUE.equals(includeChildren),
                        Person::getOrgId, orgId)''', 1)
    s = s.replace('''        IPage<Person> page = personMapper.selectPage(new Page<>(pageNum, pageSize), qw);''',
                  '''        // 含下级：按 org_path 前缀取整棵子树（组织是树，见 bp_iam_org 的 parent_id/org_path）
        if (orgId != null && Boolean.TRUE.equals(includeChildren)) {
            java.util.List<Long> ids = orgSubtreeIds(orgId);
            if (ids.isEmpty()) {
                return PageResult.of(0, pageNum, pageSize, new java.util.ArrayList<>());
            }
            qw.in(Person::getOrgId, ids);
        }
        IPage<Person> page = personMapper.selectPage(new Page<>(pageNum, pageSize), qw);''', 1)
    # 注入 orgMapper + 子树查询
    s = s.replace('''    private final PersonMapper personMapper;''',
                  '''    private final PersonMapper personMapper;
    private final com.yundao.bp.iam.mapper.IamOrgMapper orgMapper;

    /** 取某组织及其所有下级组织的 ID（按 org_path 前缀匹配） */
    private java.util.List<Long> orgSubtreeIds(Long orgId) {
        java.util.List<Long> ids = new java.util.ArrayList<>();
        com.yundao.bp.iam.entity.IamOrg self =
                orgMapper.selectById(orgId);
        if (self == null) {
            ids.add(orgId);
            return ids;
        }
        String path = self.getOrgPath();
        java.util.List<com.yundao.bp.iam.entity.IamOrg> all = orgMapper.selectList(null);
        for (com.yundao.bp.iam.entity.IamOrg o : all) {
            boolean isSelf = o.getId().equals(orgId);
            boolean under = path != null && o.getOrgPath() != null && o.getOrgPath().startsWith(path);
            if (isSelf || under) {
                ids.add(o.getId());
            }
        }
        return ids;
    }''', 1)
    io.open(ip, 'w', encoding='utf-8', newline='').write(s)
    print('PersonServiceImpl：已加子树过滤')

# 构造函数补 orgMapper 参数（若使用 @RequiredArgsConstructor 则跳过）
s = io.open(ip, encoding='utf-8').read()
if 'public PersonServiceImpl(' in s and 'orgMapper' not in s.split('public PersonServiceImpl(')[1][:400]:
    s = s.replace('''    public PersonServiceImpl(PersonMapper personMapper''',
                  '''    public PersonServiceImpl(PersonMapper personMapper,
                             com.yundao.bp.iam.mapper.IamOrgMapper orgMapper''', 1)
    s = s.replace('        this.personMapper = personMapper;',
                  '''        this.personMapper = personMapper;
        this.orgMapper = orgMapper;''', 1)
    io.open(ip, 'w', encoding='utf-8', newline='').write(s)
    print('PersonServiceImpl：构造函数已注入 orgMapper')

# ---------- 4. 前端 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Persons.vue')
s = io.open(P, encoding='utf-8').read()
if 'includeChildren' not in s:
    s = s.replace('''        <el-option v-for="o in orgOptions" :key="o.id"
                   :label="orgOptionLabel(o)" :value="Number(o.id)" />
      </el-select>''',
                  '''        <el-option v-for="o in orgOptions" :key="o.id"
                   :label="orgOptionLabel(o)" :value="Number(o.id)" />
      </el-select>
      <el-checkbox v-model="includeChildren" :disabled="!orgId"
                   data-testid="person-org-children">含下级</el-checkbox>''', 1)
    s = s.replace("const orgId = ref(null)", "const orgId = ref(null)\n/** 组织筛选是否包含下级组织 */\nconst includeChildren = ref(false)", 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('Persons.vue：已加「含下级」勾选项')
