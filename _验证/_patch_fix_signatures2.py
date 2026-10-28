# -*- coding: utf-8 -*-
"""修接口默认方法、VO 构造、换房分页实现。"""
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


patch(os.path.join(BE, 'biz', 'dto', 'TerminationVO.java'), [
    ('''                e.getBanReapplyEndDate(), ready, overdue, e.getCreateTime());''',
     '''                e.getBanReapplyEndDate(), ready, overdue, e.getCreateTime(),
                null, null, null, null, null, null, null, null, null);''', 'VO 构造补 null'),
])

patch(os.path.join(BE, 'biz', 'service', 'TerminationService.java'), [
    ('''    PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                   Long contractId, Long houseId, String keyword, Long orgId);''',
     '''    PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                   Long contractId, Long houseId, String keyword, Long orgId);

    /** 兼容旧调用：不带组织筛选。 */
    default PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                           Long contractId, Long houseId, String keyword) {
        return page(pageNum, pageSize, type, status, contractId, houseId, keyword, null);
    }''', '接口默认方法'),
])

# 换房实现：补两个重载
patch(os.path.join(BE, 'biz', 'service', 'impl', 'ExchangeServiceImpl.java'), [
    ('''    @Override
    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status) {''',
     '''    @Override
    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status) {
        return page(pageNum, pageSize, personId, oldContractId, status, null, null);
    }

    @Override
    public PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId,
                                       Long oldContractId, String status,
                                       String keyword, Long orgId) {''', '换房分页重载'),
    ('''        applyDataScope(qw, BizExchange::getPersonId, BizExchange::getPersonId, false);''',
     '''        if (orgId != null) {
            qw.apply("person_id in (select id from bp_person where org_id = {0})", orgId);
        }
        if (keyword != null && !keyword.isBlank()) {
            qw.apply("person_id in (select id from bp_person "
                    + "where person_name like concat('%', {0}, '%'))", keyword);
        }
        applyDataScope(qw, BizExchange::getPersonId, BizExchange::getPersonId, false);''',
     '换房筛选'),
])
