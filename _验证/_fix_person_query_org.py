# -*- coding: utf-8 -*-
"""人员档案相关页面的四项改进：

1. 保障档案 / 实名核验：查询条件由「人员ID」改为关键字（姓名/手机/证件号），与人员档案一致
   —— 后端两个分页接口加 keyword：先按关键字查人员 ID，再 IN 过滤
2. 实名核验方式显示中文（enums.js 增加 verifyType 映射）
3. 已通过的核验记录不再显示「实名核验」按钮（改为「重新核验」需显式点击更稳妥，这里直接隐藏）
4. 人员档案列表增加「组织名称」列（前端用已加载的组织选项做映射，无需后端改动）
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'person')
FE = os.path.join(ROOT, 'frontend', 'src')


def patch(path, pairs, label):
    s = io.open(path, encoding='utf-8').read()
    hit = 0
    for a, b in pairs:
        if a in s:
            s = s.replace(a, b, 1)
            hit += 1
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    print('%s：命中 %d/%d' % (label, hit, len(pairs)))


# ---------- 后端：两个 service 接口 + 控制器 + 实现 ----------
patch(os.path.join(J, 'service', 'GuaranteeProfileService.java'), [
    ('''    PageResult<PersonGuaranteeProfile> page(long pageNum, long pageSize,''',
     '''    PageResult<PersonGuaranteeProfile> page(long pageNum, long pageSize,'''),
    ('String profileStatus);', 'String profileStatus, String keyword);'),
], '保障档案 service 接口')

patch(os.path.join(J, 'service', 'VerifyRecordService.java'), [
    ('String verifyType, Boolean passOnly);', 'String verifyType, Boolean passOnly, String keyword);'),
], '实名核验 service 接口')

# 控制器：加 keyword 参数并透传
gc = os.path.join(J, 'controller', 'GuaranteeProfileController.java')
s = io.open(gc, encoding='utf-8').read()
if 'String keyword' not in s:
    s = s.replace('''            @RequestParam(required = false) String profileStatus) {''',
                  '''            @RequestParam(required = false) String profileStatus,
            @RequestParam(required = false) String keyword) {''', 1)
    s = s.replace('''service.page(pageNum, pageSize, securityType, incomeLevel,
                profileStatus)''', '''service.page(pageNum, pageSize, securityType, incomeLevel,
                profileStatus, keyword)''', 1)
    io.open(gc, 'w', encoding='utf-8', newline='').write(s)
    print('保障档案控制器：已加 keyword')

vc = os.path.join(J, 'controller', 'VerifyRecordController.java')
s = io.open(vc, encoding='utf-8').read()
if 'String keyword' not in s:
    s = s.replace('''            @RequestParam(required = false) Boolean passOnly) {''',
                  '''            @RequestParam(required = false) Boolean passOnly,
            @RequestParam(required = false) String keyword) {''', 1)
    s = s.replace('service.page(pageNum, pageSize, personId, verifyType, passOnly)',
                  'service.page(pageNum, pageSize, personId, verifyType, passOnly, keyword)')
    io.open(vc, 'w', encoding='utf-8', newline='').write(s)
    print('实名核验控制器：已加 keyword')

# 实现：把关键字解析成人员 ID 集合
HELPER = '''
    /** 关键字 → 人员 ID 集合（姓名/手机/证件号模糊）；无匹配返回空集合 */
    private java.util.List<Long> personIdsByKeyword(String keyword) {
        if (keyword == null || keyword.isBlank()) {
            return null;
        }
        String k = keyword.trim();
        java.util.List<com.yundao.bp.person.entity.Person> list =
                personMapper.selectList(new com.baomidou.mybatisplus.core.conditions.query
                        .LambdaQueryWrapper<com.yundao.bp.person.entity.Person>()
                        .and(w -> w.like(com.yundao.bp.person.entity.Person::getPersonName, k)
                                .or().like(com.yundao.bp.person.entity.Person::getPhone, k)
                                .or().like(com.yundao.bp.person.entity.Person::getIdCard, k))
                        .last("limit 500"));
        java.util.List<Long> ids = new java.util.ArrayList<>();
        for (com.yundao.bp.person.entity.Person p : list) {
            ids.add(p.getId());
        }
        return ids;
    }
'''

gp = os.path.join(J, 'service', 'impl', 'GuaranteeProfileServiceImpl.java')
s = io.open(gp, encoding='utf-8').read()
if 'personIdsByKeyword' not in s:
    s = s.replace('''                                                   String profileStatus) {''',
                  '''                                                   String profileStatus, String keyword) {''', 1)
    s = s.replace('''                        .orderByDesc(PersonGuaranteeProfile::getId);''',
                  '''                        .orderByDesc(PersonGuaranteeProfile::getId);
        java.util.List<Long> kwIds = personIdsByKeyword(keyword);
        if (kwIds != null) {
            if (kwIds.isEmpty()) {
                return PageResult.of(0, pageNum, pageSize, new ArrayList<>());
            }
            qw.in(PersonGuaranteeProfile::getPersonId, kwIds);
        }''', 1)
    # 在 fillPersonInfo 前插入 helper
    s = s.replace('    /** 给档案列表补齐人员姓名与脱敏信息（办理人员需要一眼看出是谁） */',
                  HELPER + '\n    /** 给档案列表补齐人员姓名与脱敏信息（办理人员需要一眼看出是谁） */', 1)
    io.open(gp, 'w', encoding='utf-8', newline='').write(s)
    print('保障档案实现：已加 keyword 过滤')

vp = os.path.join(J, 'service', 'impl', 'VerifyRecordServiceImpl.java')
s = io.open(vp, encoding='utf-8').read()
if 'personIdsByKeyword' not in s:
    s = s.replace('''                                               String verifyType, Boolean passOnly) {''',
                  '''                                               String verifyType, Boolean passOnly,
                                               String keyword) {''', 1)
    s = s.replace('''                        .eq(personId != null, PersonVerifyRecord::getPersonId, personId)''',
                  '''                        .eq(personId != null, PersonVerifyRecord::getPersonId, personId)''', 1)
    s = s.replace('''        IPage<PersonVerifyRecord> page = mapper.selectPage(''',
                  '''        java.util.List<Long> kwIds = personIdsByKeyword(keyword);
        if (kwIds != null) {
            if (kwIds.isEmpty()) {
                return PageResult.of(0, pageNum, pageSize, new java.util.ArrayList<>());
            }
            qw.in(PersonVerifyRecord::getPersonId, kwIds);
        }
        IPage<PersonVerifyRecord> page = mapper.selectPage(''', 1)
    s = s.replace('    /** 给核验流水补齐人员姓名与脱敏手机/证件号 */',
                  HELPER + '\n    /** 给核验流水补齐人员姓名与脱敏手机/证件号 */', 1)
    io.open(vp, 'w', encoding='utf-8', newline='').write(s)
    print('实名核验实现：已加 keyword 过滤')

# ---------- 前端：enums.js 加 verifyType 中文 ----------
en = os.path.join(FE, 'constants', 'enums.js')
s = io.open(en, encoding='utf-8').read()
if 'verifyType:' not in s:
    s = s.replace('const TYPE_OVERRIDE = {\n',
                  "const TYPE_OVERRIDE = {\n"
                  "  // 实名核验方式（后端 verifyType 是英文编码）\n"
                  "  verifyType: {\n"
                  "    FACE_COMPARE: '人脸比对',\n"
                  "    IDCARD_FACE: '身份证+人脸',\n"
                  "    IDCARD_TWO_FACTOR: '身份证二要素',\n"
                  "    IDCARD_THREE_FACTOR: '身份证三要素',\n"
                  "    OCR_IDCARD: 'OCR 识别',\n"
                  "    MANUAL: '人工核验'\n"
                  "  },\n", 1)
    io.open(en, 'w', encoding='utf-8', newline='').write(s)
    print('enums.js：已加 verifyType 中文')
else:
    print('enums.js：已有 verifyType')

# ---------- 前端：Persons.vue ----------
P = os.path.join(FE, 'views', 'Persons.vue')
s = io.open(P, encoding='utf-8').read()
changed = []

# 1) 保障档案查询：人员ID → 关键字
if 'gQuery.personId' in s or 'profilePersonId' in s:
    s = re.sub(r'<el-input v-model="profilePersonId"[^/]*/>',
               '<el-input v-model="gQuery.keyword" placeholder="姓名 / 手机 / 证件号" clearable\n'
               '                    style="width:220px" data-testid="profile-keyword"\n'
               '                    @keyup.enter="loadProfiles" />', s, count=1)
    changed.append('保障档案关键字框')

# 2) 实名核验查询：人员ID → 关键字（列表过滤）
s = s.replace('''<el-input v-model="verifyPersonId" placeholder="人员ID 查看结论"
                    style="width:200px" />''',
              '''<el-input v-model="vQuery.keyword" placeholder="姓名 / 手机 / 证件号" clearable
                    style="width:220px" data-testid="verify-keyword"
                    @keyup.enter="loadVerifies" />''', 1)
if 'verify-keyword' in s:
    changed.append('实名核验关键字框')

# 3) 已通过的不再显示「实名核验」按钮
s = s.replace('''<el-button link type="primary" @click="openVerifyFor(row)">实名核验</el-button>''',
              '''<el-button v-if="Number(row.verifyPass) !== 1" link type="primary"
                         @click="openVerifyFor(row)">实名核验</el-button>
              <span v-else class="muted">已通过</span>''', 1)
if 'Number(row.verifyPass) !== 1' in s:
    changed.append('已通过隐藏按钮')

# 4) 人员档案列表加「组织」列（用已加载的组织选项映射名称）
s = s.replace('''<el-table-column prop="personName" label="姓名" width="110" />''',
              '''<el-table-column prop="personName" label="姓名" width="110" />
          <el-table-column label="所属组织" min-width="160">
            <template #default="{ row }">{{ orgNameOf(row.orgId) }}</template>
          </el-table-column>''', 1)
if 'orgNameOf(row.orgId)' in s:
    changed.append('组织列')

if 'function orgNameOf' not in s:
    s = s.replace('async function loadOrgOptions() {',
                  '''function orgNameOf(id) {
  const hit = orgOptions.value.find((o) => Number(o.id) === Number(id))
  return hit ? hit.orgName : (id ? id : '-')
}
async function loadOrgOptions() {''', 1)
    changed.append('orgNameOf')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Persons.vue：', '、'.join(changed) if changed else '（无改动）')
