package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.dto.CohabitantCreateCmd;
import com.yundao.bp.biz.dto.CohabitantVO;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.entity.BizContractCohabitant;
import com.yundao.bp.biz.mapper.BizContractCohabitantMapper;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.biz.service.CohabitantService;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 合同同住人实现。
 */
@Service
public class CohabitantServiceImpl implements CohabitantService {

    private static final Logger log = LoggerFactory.getLogger(CohabitantServiceImpl.class);

    private final BizContractCohabitantMapper mapper;
    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;

    public CohabitantServiceImpl(BizContractCohabitantMapper mapper,
                                 BizContractMapper contractMapper,
                                 SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CohabitantVO add(Long contractId, CohabitantCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        BizContract ct = contractMapper.selectById(contractId);
        if (ct == null) {
            throw BizException.notFound("合同");
        }
        ContractStatus st;
        try {
            st = ContractStatus.valueOf(ct.getContractStatus());
        } catch (IllegalArgumentException e) {
            st = ContractStatus.DRAFT;
        }
        if (st.isTerminal()) {
            throw BizException.stateConflict("合同已" + st.label() + "，不可添加同住人");
        }
        // 同一合同内姓名不可重复
        Long dup = mapper.selectCount(new LambdaQueryWrapper<BizContractCohabitant>()
                .eq(BizContractCohabitant::getContractId, contractId)
                .eq(BizContractCohabitant::getMemberName, cmd.memberName().trim()));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("该合同已有同名同住人：" + cmd.memberName().trim());
        }

        long id = idGen.nextId();
        BizContractCohabitant e = new BizContractCohabitant();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setContractId(contractId);
        e.setPersonId(cmd.personId());
        e.setMemberName(cmd.memberName().trim());
        e.setIdCardMask(cmd.idCardMask());
        e.setRelation(normalizeRelation(cmd.relation()));
        e.setIsGranted(cmd.isGranted() == null ? 0 : cmd.isGranted());
        e.setCreateTime(LocalDateTime.now());
        mapper.insert(e);
        log.info("合同 {} 添加同住人 {}（{}）", ct.getContractNo(), e.getMemberName(),
                CohabitantVO.relationLabel(e.getRelation()));
        return CohabitantVO.from(e);
    }

    @Override
    public List<CohabitantVO> list(Long contractId) {
        return mapper.selectList(new LambdaQueryWrapper<BizContractCohabitant>()
                        .eq(BizContractCohabitant::getContractId, contractId)
                        .orderByAsc(BizContractCohabitant::getId))
                .stream().map(CohabitantVO::from).toList();
    }

    @Override
    public CohabitantVO get(Long id) {
        BizContractCohabitant e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("同住人");
        }
        return CohabitantVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void remove(Long id) {
        BizContractCohabitant e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("同住人");
        }
        mapper.deleteById(id);
        log.info("合同 {} 移除同住人 {}", e.getContractId(), e.getMemberName());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CohabitantVO setGranted(Long id, boolean granted) {
        BizContractCohabitant e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("同住人");
        }
        e.setIsGranted(granted ? 1 : 0);
        mapper.updateById(e);
        return CohabitantVO.from(e);
    }

    @Override
    public int householdSize(Long contractId) {
        Long n = mapper.selectCount(new LambdaQueryWrapper<BizContractCohabitant>()
                .eq(BizContractCohabitant::getContractId, contractId));
        return 1 + (n == null ? 0 : n.intValue());
    }

    private static String normalizeRelation(String relation) {
        if (relation == null || relation.isBlank()) {
            return "OTHER";
        }
        return switch (relation) {
            case "SPOUSE", "CHILD", "PARENT", "SIBLING" -> relation;
            default -> "OTHER";
        };
    }
}
