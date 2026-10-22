# -*- coding: utf-8 -*-
"""公示中签名单：Service 方法 + Controller 接口 + 建表字段。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
B = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'biz')

# ---- Controller ----
C = os.path.join(B, 'controller', 'PublicityReviewController.java')
s = io.open(C, encoding='utf-8').read()
if 'winners' not in s:
    block = '''
    /** 公示中签名单（身份证脱敏）。 */
    @GetMapping("/publicities/{id}/winners")
    @RequirePerm("biz:publicity:view")
    public R<java.util.List<com.yundao.bp.biz.dto.PublicityWinnerVO>> winners(
            @PathVariable Long id) {
        return R.ok(service.winners(id));
    }
'''
    anchor = '    @PostMapping("/publicities/{id}/publish")'
    if anchor in s:
        s = s.replace(anchor, block + '\n' + anchor, 1)
    else:
        i = s.rstrip().rfind('}')
        s = s[:i] + block + s[i:]
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('Controller：/winners 已加')

# ---- Service 接口 ----
S = os.path.join(B, 'service', 'PublicityService.java')
s = io.open(S, encoding='utf-8').read()
if 'winners' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + ('\n    /** 公示中签名单。 */\n'
                 '    java.util.List<com.yundao.bp.biz.dto.PublicityWinnerVO> winners(Long publicityId);\n') + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('Service：winners 已加')

# ---- Service 实现 ----
I = os.path.join(B, 'service', 'impl', 'PublicityServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'winners(' not in s:
    inject = '''
    /** 人员（中签人姓名/脱敏证件） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonMapper winnerPersonMapper;

    /** 摇号结果 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizLotteryResultMapper winnerLotteryMapper;

    /** 房源（中签房号） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper winnerHouseMapper;
'''
    j = s.find('    public PublicityServiceImpl(')
    if j < 0:
        j = s.find('    private final ')
    s = s[:j] + inject + '\n' + s[j:]

    impl = '''
    @Override
    public java.util.List<com.yundao.bp.biz.dto.PublicityWinnerVO> winners(Long publicityId) {
        com.yundao.bp.biz.entity.BizPublicity p = mapper.selectById(publicityId);
        if (p == null || p.getBatchId() == null) {
            return java.util.List.of();
        }
        java.util.List<com.yundao.bp.biz.entity.BizLotteryResult> results =
                winnerLotteryMapper.selectList(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                <com.yundao.bp.biz.entity.BizLotteryResult>()
                                .eq(com.yundao.bp.biz.entity.BizLotteryResult::getBatchId,
                                        p.getBatchId())
                                .orderByAsc(com.yundao.bp.biz.entity.BizLotteryResult::getLotterySeq));
        if (results.isEmpty()) {
            return java.util.List.of();
        }
        java.util.Set<Long> personIds = new java.util.HashSet<>();
        java.util.Set<Long> houseIds = new java.util.HashSet<>();
        for (com.yundao.bp.biz.entity.BizLotteryResult r : results) {
            if (r.getPersonId() != null) {
                personIds.add(r.getPersonId());
            }
            if (r.getHouseId() != null) {
                houseIds.add(r.getHouseId());
            }
        }
        java.util.Map<Long, com.yundao.bp.person.entity.Person> persons = new java.util.HashMap<>();
        if (!personIds.isEmpty()) {
            for (com.yundao.bp.person.entity.Person person
                    : winnerPersonMapper.selectBatchIds(personIds)) {
                persons.put(person.getId(), person);
            }
        }
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetHouse> houses = new java.util.HashMap<>();
        if (!houseIds.isEmpty()) {
            for (com.yundao.bp.asset.entity.AssetHouse house
                    : winnerHouseMapper.selectBatchIds(houseIds)) {
                houses.put(house.getId(), house);
            }
        }
        java.util.List<com.yundao.bp.biz.dto.PublicityWinnerVO> out = new java.util.ArrayList<>();
        for (com.yundao.bp.biz.entity.BizLotteryResult r : results) {
            com.yundao.bp.person.entity.Person person = persons.get(r.getPersonId());
            com.yundao.bp.asset.entity.AssetHouse house = houses.get(r.getHouseId());
            String type = r.getResultType();
            String typeLabel = "WIN".equals(type) ? "中签"
                    : ("WAIT".equals(type) || "BACKUP".equals(type) ? "候补" : "未中签");
            out.add(new com.yundao.bp.biz.dto.PublicityWinnerVO(
                    r.getPersonId(),
                    person == null ? null : person.getRealName(),
                    person == null ? null : person.getIdCardMask(),
                    maskPhone(person == null ? null : person.getPhone()),
                    house == null ? null : house.getHouseName(),
                    r.getLotterySeq(),
                    r.getSelectSeq(),
                    type,
                    typeLabel));
        }
        return out;
    }

    /** 手机号脱敏：139****0000 */
    private String maskPhone(String phone) {
        if (phone == null || phone.length() < 7) {
            return phone;
        }
        return phone.substring(0, 3) + "****" + phone.substring(phone.length() - 4);
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('ServiceImpl：winners 已实现')

print('写入完成（mapper 字段名需编译校验）')
