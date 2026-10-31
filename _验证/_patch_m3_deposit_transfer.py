# -*- coding: utf-8 -*-
import io

# 押金状态补充“已转移”
p = r'..\backend\src\main\java\com\yundao\bp\fin\constant\DepositStatus.java'
s = io.open(p, encoding='utf-8').read()
if 'TRANSFERRED' not in s:
    s = s.replace('    DEDUCTED("', '    TRANSFERRED("已转移"),\n    DEDUCTED("')
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('DepositStatus TRANSFERRED')

# 换房：押金转移
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
    # 构造器参数
    s = s.replace('''                                 BizContractMapper contractMapper,
                                 SnowflakeIdGenerator idGen) {''',
                  '''                                 BizContractMapper contractMapper,
                                 SnowflakeIdGenerator idGen,
                                 com.yundao.bp.fin.mapper.FinDepositMapper depositMapper,
                                 com.yundao.bp.fin.mapper.DepositTransferMapper transferMapper,
                                 org.springframework.jdbc.core.JdbcTemplate jdbc) {''', 1)
    s = s.replace('''        this.contractMapper = contractMapper;
        this.idGen = idGen;''',
                  '''        this.contractMapper = contractMapper;
        this.idGen = idGen;
        this.depositMapper = depositMapper;
        this.transferMapper = transferMapper;
        this.jdbc = jdbc;''', 1)
    # 在生成新合同后转移押金
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
                "select count(*) from bp_fin_refund where contract_id=? and refund_status in ('PENDING','APPROVED')",
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
    print('exchange deposit transfer')
