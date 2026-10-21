# -*- coding: utf-8 -*-
"""换房落地：生成新合同 + 终止原合同 + 调整房源状态"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
p = os.path.join(BASE, r'biz\service\impl\ExchangeServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

if 'newContractId' in s and 'createNewContract' in s:
    print('已落地，跳过')
    raise SystemExit

# ---------- 1) imports ----------
s = s.replace('import com.yundao.bp.biz.constant.ExchangeStatus;',
              'import com.yundao.bp.asset.constant.HouseStatus;\n'
              'import com.yundao.bp.biz.constant.ContractStatus;\n'
              'import com.yundao.bp.biz.constant.ExchangeStatus;', 1)
s = s.replace('import com.yundao.bp.biz.entity.BizExchange;',
              'import com.yundao.bp.biz.entity.BizContract;\n'
              'import com.yundao.bp.biz.entity.BizExchange;', 1)
s = s.replace('import com.yundao.bp.biz.mapper.BizExchangeMapper;',
              'import com.yundao.bp.biz.mapper.BizContractMapper;\n'
              'import com.yundao.bp.biz.mapper.BizExchangeMapper;', 1)
s = s.replace('import java.time.LocalDateTime;',
              'import java.time.LocalDate;\n'
              'import java.time.LocalDateTime;\n'
              'import java.time.temporal.ChronoUnit;', 1)

# ---------- 2) 注入合同 Mapper ----------
s = s.replace('''    private final BizExchangeMapper mapper;
    private final AssetHouseMapper houseMapper;
    private final SnowflakeIdGenerator idGen;

    public ExchangeServiceImpl(BizExchangeMapper mapper, AssetHouseMapper houseMapper,
                               SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.houseMapper = houseMapper;
        this.idGen = idGen;
    }''',
              '''    private final BizExchangeMapper mapper;
    private final AssetHouseMapper houseMapper;
    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;

    public ExchangeServiceImpl(BizExchangeMapper mapper, AssetHouseMapper houseMapper,
                               BizContractMapper contractMapper,
                               SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.houseMapper = houseMapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
    }''', 1)

# ---------- 3) 重写 complete()：真正落地 ----------
old_complete = '''    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExchangeVO complete(Long id) {
        BizExchange e = require(id);
        transition(e, ExchangeStatus.COMPLETED);
        // 权限迁移：换房后需把原房源的开门权限迁到新房源
        e.setGrantMigrated(1);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        AssetHouse newHouse = houseMapper.selectById(e.getNewHouseId());
        log.info("⭐ 换房完成 {}：人员 {} 房源 {} → {}（{}），权限已迁移",
                e.getExchangeNo(), e.getPersonId(), e.getOldHouseId(), e.getNewHouseId(),
                newHouse == null ? "" : newHouse.getHouseCode());
        return ExchangeVO.from(e);
    }'''

new_complete = '''    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExchangeVO complete(Long id) {
        BizExchange e = require(id);
        transition(e, ExchangeStatus.COMPLETED);

        BizContract oldCt = e.getOldContractId() == null ? null
                : contractMapper.selectById(e.getOldContractId());
        AssetHouse newHouse = houseMapper.selectById(e.getNewHouseId());
        if (newHouse == null) {
            throw BizException.notFound("新房源");
        }

        // ① 生成新合同（延续原止租日、换到新房源、直接生效）
        Long newContractId = null;
        if (oldCt != null) {
            newContractId = createNewContract(e, oldCt, newHouse);
            e.setNewContractId(newContractId);

            // ② 原合同终止（换房退出）
            oldCt.setContractStatus(ContractStatus.TERMINATED.name());
            oldCt.setTerminateReason("换房退出（换房单 " + e.getExchangeNo() + "）");
            oldCt.setUpdateTime(LocalDateTime.now());
            contractMapper.updateById(oldCt);

            // ③ 旧房源回可配池
            AssetHouse oldHouse = houseMapper.selectById(e.getOldHouseId());
            if (oldHouse != null) {
                oldHouse.setHouseStatus(HouseStatus.VACANT.name());
                oldHouse.setUpdateTime(LocalDateTime.now());
                houseMapper.updateById(oldHouse);
            }
        }

        // ④ 新房源置已入住
        newHouse.setHouseStatus(HouseStatus.OCCUPIED.name());
        newHouse.setUpdateTime(LocalDateTime.now());
        houseMapper.updateById(newHouse);

        // ⑤ 权限迁移
        e.setGrantMigrated(1);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        log.info("⭐⭐ 换房完成 {}：人员 {} 房源 {} → {}，新合同 {}，原合同已终止，旧房源已回池",
                e.getExchangeNo(), e.getPersonId(), e.getOldHouseId(), e.getNewHouseId(),
                newContractId);
        return ExchangeVO.from(e);
    }

    /**
     * 生成换房后的新合同。
     *
     * <p>规则：<b>延续原合同的止租日与租金</b>，只换房源与空间；
     * 租期起始日为换房当日。新合同 {@code parentContractId} 指向原合同，便于追溯链条。
     */
    private Long createNewContract(BizExchange e, BizContract oldCt, AssetHouse newHouse) {
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        BizContract nc = new BizContract();
        nc.setId(id);
        nc.setTenantId(oldCt.getTenantId());
        nc.setContractNo("BC" + id);
        nc.setContractType(oldCt.getContractType());
        nc.setTemplateId(oldCt.getTemplateId());
        nc.setOrgId(oldCt.getOrgId());
        nc.setAccountSetId(oldCt.getAccountSetId());
        nc.setLesseePersonId(oldCt.getLesseePersonId());
        nc.setLesseeName(oldCt.getLesseeName());
        nc.setLesseePhone(oldCt.getLesseePhone());
        nc.setLesseeIdCardMask(oldCt.getLesseeIdCardMask());
        nc.setLessorOrgId(oldCt.getLessorOrgId());

        // 换房核心：房源与空间换成新的
        nc.setHouseId(e.getNewHouseId());
        nc.setSpaceId(newHouse.getSpaceId());
        nc.setHouseAddress(newHouse.getHouseName());
        nc.setHouseArea(newHouse.getArea());

        // 延续止租日，起始日为换房当日
        LocalDate start = LocalDate.now();
        LocalDate end = oldCt.getLeaseEnd();
        nc.setLeaseStart(start);
        nc.setLeaseEnd(end);
        if (end != null && end.isAfter(start)) {
            long months = ChronoUnit.MONTHS.between(start, end);
            nc.setLeaseMonths((int) Math.max(1, months));
        } else {
            nc.setLeaseMonths(1);
        }

        nc.setRentPrice(oldCt.getRentPrice());
        nc.setRentUnit(oldCt.getRentUnit());
        nc.setMonthlyRent(oldCt.getMonthlyRent());
        nc.setDepositAmount(oldCt.getDepositAmount());
        nc.setSubsidyAmount(oldCt.getSubsidyAmount());
        nc.setActualPay(oldCt.getActualPay());
        nc.setPayCycle(oldCt.getPayCycle());
        nc.setPayDay(oldCt.getPayDay());
        nc.setLateFeeRate(oldCt.getLateFeeRate());
        nc.setSignType(oldCt.getSignType());

        // 换房非新签，直接履约中
        nc.setContractStatus(ContractStatus.EFFECTIVE.name());
        nc.setParentContractId(oldCt.getId());
        nc.setAutoGrant(oldCt.getAutoGrant());
        nc.setAutoExpire(oldCt.getAutoExpire());
        nc.setArrearsStop(oldCt.getArrearsStop());
        nc.setRemark("换房生成（换房单 " + e.getExchangeNo() + "）");
        nc.setIsDeleted(0);
        nc.setCreateTime(now);
        nc.setUpdateTime(now);
        contractMapper.insert(nc);
        log.info("换房生成新合同 {}：房源 {} 租期 {}~{}", nc.getContractNo(),
                e.getNewHouseId(), start, end);
        return id;
    }'''

assert old_complete in s, 'complete 锚点缺失'
s = s.replace(old_complete, new_complete, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ 换房落地：新合同 + 原合同终止 + 房源状态')
