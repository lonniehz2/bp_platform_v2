package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.entity.FinFeeType;
import com.yundao.bp.fin.mapper.FinFeeTypeMapper;
import com.yundao.bp.fin.service.FeeTypeService;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class FeeTypeServiceImpl implements FeeTypeService {

    private final FinFeeTypeMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public FeeTypeServiceImpl(FinFeeTypeMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    // scope:ignore 费用类型是租户级字典（公共数据），不按组织过滤
    public List<FinFeeType> list(boolean enabledOnly) {
        LambdaQueryWrapper<FinFeeType> qw = new LambdaQueryWrapper<FinFeeType>()
                .orderByAsc(FinFeeType::getSortNo)
                .orderByAsc(FinFeeType::getId);
        if (enabledOnly) {
            qw.eq(FinFeeType::getStatus, "ENABLED");
        }
        return mapper.selectList(qw);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FinFeeType create(String code, String name, Integer sortNo) {
        if (code == null || code.isBlank()) {
            throw BizException.paramInvalid("类型编码不能为空");
        }
        if (name == null || name.isBlank()) {
            throw BizException.paramInvalid("类型名称不能为空");
        }
        Long dup = mapper.selectCount(new LambdaQueryWrapper<FinFeeType>()
                .eq(FinFeeType::getTypeCode, code.trim()));
        if (dup != null && dup > 0) {
            throw new BizException(ErrorCode.DUPLICATED, "类型编码已存在：" + code);
        }
        LocalDateTime now = LocalDateTime.now();
        FinFeeType e = new FinFeeType();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setTypeCode(code.trim().toUpperCase());
        e.setTypeName(name.trim());
        e.setStatus("ENABLED");
        e.setSortNo(sortNo == null ? 100 : sortNo);
        e.setIsDeleted(0);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        return e;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FinFeeType update(Long id, String code, String name, Integer sortNo) {
        FinFeeType e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("费用类型");
        }
        if (code != null && !code.isBlank() && !code.trim().equalsIgnoreCase(e.getTypeCode())) {
            Long dup = mapper.selectCount(new LambdaQueryWrapper<FinFeeType>()
                    .eq(FinFeeType::getTypeCode, code.trim().toUpperCase()));
            if (dup != null && dup > 0) {
                throw new BizException(ErrorCode.DUPLICATED, "类型编码已存在：" + code);
            }
            e.setTypeCode(code.trim().toUpperCase());
        }
        if (name != null && !name.isBlank()) {
            e.setTypeName(name.trim());
        }
        if (sortNo != null) {
            e.setSortNo(sortNo);
        }
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return e;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FinFeeType setStatus(Long id, boolean enabled) {
        FinFeeType e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("费用类型");
        }
        e.setStatus(enabled ? "ENABLED" : "DISABLED");
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return e;
    }
}
