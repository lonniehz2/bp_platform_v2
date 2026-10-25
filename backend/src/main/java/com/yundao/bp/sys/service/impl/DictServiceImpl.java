package com.yundao.bp.sys.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.entity.SysDict;
import com.yundao.bp.sys.mapper.SysDictMapper;
import com.yundao.bp.sys.service.DictService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 数据字典实现。
 */
@Service
public class DictServiceImpl implements DictService {

    private final SysDictMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public DictServiceImpl(SysDictMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    public List<SysDict> listByType(String dictType) {
        String tenant = TenantContext.get() == null ? null : TenantContext.tenantId();
        List<SysDict> all = mapper.selectByTypeIgnoreTenant(dictType);
        // 租户配置优先覆盖系统内置
        Map<String, SysDict> merged = new LinkedHashMap<>();
        for (SysDict d : all) {
            if (d.getTenantId() == null || d.getTenantId().isBlank()) {
                merged.putIfAbsent(d.getDictCode(), d);
            }
        }
        if (tenant != null) {
            for (SysDict d : all) {
                if (tenant.equals(d.getTenantId())) {
                    merged.put(d.getDictCode(), d);
                }
            }
        }
        List<SysDict> out = new ArrayList<>(merged.values());
        out.sort((a, b) -> {
            int x = a.getSortNo() == null ? 0 : a.getSortNo();
            int y = b.getSortNo() == null ? 0 : b.getSortNo();
            return x != y ? Integer.compare(x, y)
                    : Long.compare(a.getId(), b.getId());
        });
        return out;
    }

    @Override
    public List<SysDict> listByType(String dictType, boolean includeDisabled) {
        if (!includeDisabled) {
            return listByType(dictType);
        }
        // 管理页：含已停用，便于重新启用
        return mapper.selectByTypeAll(dictType);
    }

    @Override
    public Map<String, String> mapByType(String dictType) {
        Map<String, String> m = new LinkedHashMap<>();
        for (SysDict d : listByType(dictType)) {
            m.put(d.getDictCode(), d.getDictLabel());
        }
        return m;
    }

    @Override
    public String label(String dictType, String dictCode) {
        for (SysDict d : listByType(dictType)) {
            if (d.getDictCode().equals(dictCode)) {
                return d.getDictLabel();
            }
        }
        return dictCode;
    }

    @Override
    public List<String> types() {
        // 内置字典 tenant_id 为 NULL，必须忽略租户过滤才能查到
        return mapper.distinctTypes();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SysDict create(String dictType, String dictCode, String dictLabel, String dictValue,
                          Integer sortNo, String remark) {
        if (dictType == null || dictType.isBlank() || dictCode == null || dictCode.isBlank()) {
            throw BizException.paramInvalid("字典类型与编码不能为空");
        }
        String tenant = TenantContext.tenantId();
        Long dup = mapper.selectCount(new LambdaQueryWrapper<SysDict>()
                .eq(SysDict::getTenantId, tenant)
                .eq(SysDict::getDictType, dictType)
                .eq(SysDict::getDictCode, dictCode));
        if (dup != null && dup > 0) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.DUPLICATED,
                    "该字典项已存在");
        }
        long id = idGen.nextId();
        SysDict d = new SysDict();
        d.setId(id);
        d.setTenantId(tenant);
        d.setDictType(dictType);
        d.setDictCode(dictCode);
        d.setDictLabel(dictLabel);
        d.setDictValue(dictValue);
        d.setSortNo(sortNo == null ? 0 : sortNo);
        d.setIsDefault(0);
        d.setDictStatus("ENABLED");
        d.setRemark(remark);
        d.setIsDeleted(0);
        d.setCreateTime(LocalDateTime.now());
        d.setUpdateTime(LocalDateTime.now());
        mapper.insert(d);
        return d;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SysDict setStatus(Long id, boolean enabled) {
        SysDict d = mapper.selectById(id);
        if (d == null) {
            throw BizException.notFound("字典项");
        }
        d.setDictStatus(enabled ? "ENABLED" : "DISABLED");
        d.setUpdateTime(LocalDateTime.now());
        mapper.updateById(d);
        return d;
    }
}
