# -*- coding: utf-8 -*-
"""补接口签名与实现方法。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# TerminationService
p = os.path.join(BE, 'biz', 'service', 'TerminationService.java')
s = io.open(p, encoding='utf-8').read()
if 'orgId' not in s:
    s = s.replace('''    PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                   Long contractId, Long houseId, String keyword);''',
                  '''    PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                   Long contractId, Long houseId, String keyword, Long orgId);

    /** 结算预览：押金/欠费/损坏/合计（不落库）。 */
    java.util.Map<String, Object> settlePreview(Long id);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('TerminationService 已补签名')

# ExchangeService
p = os.path.join(BE, 'biz', 'service', 'ExchangeService.java')
s = io.open(p, encoding='utf-8').read()
if 'keyword' not in s:
    s = s.replace('''    PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId, Long oldContractId,
                                String status);''',
                  '''    PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId, Long oldContractId,
                                String status);

    PageResult<ExchangeVO> page(long pageNum, long pageSize, Long personId, Long oldContractId,
                                String status, String keyword, Long orgId);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('ExchangeService 已补签名')

# ContractService + impl
p = os.path.join(BE, 'biz', 'service', 'ContractService.java')
s = io.open(p, encoding='utf-8').read()
if 'activeByPerson' not in s:
    s = s.replace('''    ContractVO get(Long id);''', '''    ContractVO get(Long id);

    /** 人员当前有效合同（无则返回 null）。 */
    ContractVO activeByPerson(Long personId);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('ContractService 已补签名')

p = os.path.join(BE, 'biz', 'service', 'impl', 'ContractServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'activeByPerson' not in s:
    s = s.replace('''    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO renew''', '''    @Override
    public ContractVO activeByPerson(Long personId) {
        if (personId == null) {
            return null;
        }
        BizContract c = mapper.selectOne(new LambdaQueryWrapper<BizContract>()
                .eq(BizContract::getLesseePersonId, personId)
                .in(BizContract::getContractStatus, "SIGNING", "EFFECTIVE", "RENEWING")
                .orderByDesc(BizContract::getId)
                .last("LIMIT 1"));
        return c == null ? null : ContractVO.from(c);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ContractVO renew''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('ContractService 实现已加')

# 修 controller settle-preview 调用
p = os.path.join(BE, 'biz', 'controller', 'TerminationController.java')
s = io.open(p, encoding='utf-8').read()
s = s.replace('return R.ok(service.settlePreview(service.requireForPreview(id)));',
              'return R.ok(service.settlePreview(id));')
io.open(p, 'w', encoding='utf-8', newline='').write(s)

# 修 impl：新增 settlePreview(Long) 包装
p = os.path.join(BE, 'biz', 'service', 'impl', 'TerminationServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
if 'public java.util.Map<String, Object> settlePreview(Long id)' not in s:
    s = s.replace('''    /** 结算预览：押金（合同）、欠费（未缴账单）、损坏赔偿（验房）、合计。 */''',
                  '''    @Override
    public java.util.Map<String, Object> settlePreview(Long id) {
        return settlePreview(require(id));
    }

    /** 结算预览：押金（合同）、欠费（未缴账单）、损坏赔偿（验房）、合计。 */''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('settlePreview 包装已加')
