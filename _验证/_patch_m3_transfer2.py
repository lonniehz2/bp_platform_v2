# -*- coding: utf-8 -*-
import io

p = r'..\backend\src\main\java\com\yundao\bp\biz\service\impl\ExchangeServiceImpl.java'
s = io.open(p, encoding='utf-8').read()

if 'transferDeposit' not in s:
    s = s.replace('''    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;''',
                  '''    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;
    private final com.yundao.bp.fin.mapper.FinDepositMapper depositMapper;
    private final com.yundao.bp.fin.mapper.DepositTransferMapper transferMapper;
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;''', 1)
    s = s.replace('''    public ExchangeServiceImpl(BizExchangeMapper mapper, AssetHouseMapper houseMapper,
                               BizContractMapper contractMapper,
                               SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.houseMapper = houseMapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
    }''',
                  '''    public ExchangeServiceImpl(BizExchangeMapper mapper, AssetHouseMapper houseMapper,
                               BizContractMapper contractMapper,
                               SnowflakeIdGenerator idGen,
                               com.yundao.bp.fin.mapper.FinDepositMapper depositMapper,
                               com.yundao.bp.fin.mapper.DepositTransferMapper transferMapper,
                               org.springframework.jdbc.core.JdbcTemplate jdbc) {
        this.mapper = mapper;
        this.houseMapper = houseMapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
        this.depositMapper = depositMapper;
        this.transferMapper = transferMapper;
        this.jdbc = jdbc;
    }''', 1)
    s = s.replace('''            newContractId = createNewContract(e, oldCt, newHouse);
            e.setNewContractId(newContractId);''',
                  '''            newContractId = createNewContract(e, oldCt, newHouse);
            e.setNewContractId(newContractId);
            transferDeposit(e, oldCt, newContractId);''', 1)
    idx = s.rfind('}')
    s = s[:idx] + '''
    /** 换房完成：押金余额全额转移到新合同，原台账置“已转移”。 */
    private void transferDeposit(BizExchange e, BizContract oldCt, Long newContractId) {
        com.yundao.bp.fin.entity.FinDeposit old = depositMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        <com.yundao.bp.fin.entity.FinDeposit>()
                        .eq(com.yundao.bp.fin.entity.FinDeposit::getContractId, oldCt.getId())
                        .orderByDesc(com.yundao.bp.fin.entity.FinDeposit::getId)
                        .last("LIMIT 1"));
        if (old == null) {
            return;
        }
        Long pending = jdbc.queryForObject(
                "select count(*) from bp_fin_refund where contract_id=?"
                        + " and refund_status in ('PENDING','APPROVED')",
                Long.class, oldCt.getId());
        if (pending != null && pending > 0) {
            throw BizException.stateConflict("原合同存在退款中的单据，请先处理后再换房");
        }
        java.math.BigDecimal amount = old.getBalanceAmount() == null
                ? java.math.BigDecimal.ZERO : old.getBalanceAmount();
        if (amount.compareTo(java.math.BigDecimal.ZERO) <= 0) {
            return;
        }
        old.setBalanceAmount(java.math.BigDecimal.ZERO);
        old.setDepositStatus("TRANSFERRED");
        old.setUpdateTime(java.time.LocalDateTime.now());
        depositMapper.updateById(old);

        com.yundao.bp.fin.entity.FinDeposit nc = new com.yundao.bp.fin.entity.FinDeposit();
        nc.setId(idGen.nextId());
        nc.setTenantId(old.getTenantId());
        nc.setContractId(newContractId);
        nc.setPersonId(old.getPersonId());
        nc.setOrgId(old.getOrgId());
        nc.setDepositAmount(amount);
        nc.setPaidAmount(amount);
        nc.setDeductAmount(java.math.BigDecimal.ZERO);
        nc.setRefundAmount(java.math.BigDecimal.ZERO);
        nc.setBalanceAmount(amount);
        nc.setDepositStatus("HELD");
        nc.setSourceType("EXCHANGE");
        nc.setSourceContractId(oldCt.getId());
        nc.setCreateTime(java.time.LocalDateTime.now());
        nc.setUpdateTime(java.time.LocalDateTime.now());
        depositMapper.insert(nc);

        com.yundao.bp.fin.entity.DepositTransfer tr =
                new com.yundao.bp.fin.entity.DepositTransfer();
        tr.setId(idGen.nextId());
        tr.setTenantId(old.getTenantId());
        tr.setExchangeId(e.getId());
        tr.setOldContractId(oldCt.getId());
        tr.setNewContractId(newContractId);
        tr.setOldDepositId(old.getId());
        tr.setNewDepositId(nc.getId());
        tr.setTransferAmount(amount);
        tr.setCreateTime(java.time.LocalDateTime.now());
        transferMapper.insert(tr);
    }
''' + s[idx:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('transfer patched')
else:
    print('already')
