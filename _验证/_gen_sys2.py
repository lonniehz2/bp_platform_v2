# -*- coding: utf-8 -*-
"""生成 sys 服务 + 接口"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

# ==================== AuditService ====================
F['sys/service/AuditService.java'] = '''package com.yundao.bp.sys.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.sys.entity.SysAuditLog;
import java.time.LocalDate;

/**
 * 审计日志服务（只追加，不提供修改/删除）。
 */
public interface AuditService {

    /** 写审计（失败不抛出，调用方自行决定是否忽略）。 */
    void record(String auditType, String auditLevel, String bizType, Long bizId,
                Long operatorId, String operatorName,
                String targetType, String targetId, String action,
                String beforeJson, String afterJson, String reason, String clientIp);

    PageResult<SysAuditLog> page(long pageNum, long pageSize, String auditType, String level,
                                 String operatorName, LocalDate dateFrom, LocalDate dateTo);

    SysAuditLog get(Long id);
}
'''

F['sys/service/impl/AuditServiceImpl.java'] = '''package com.yundao.bp.sys.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.entity.SysAuditLog;
import com.yundao.bp.sys.mapper.SysAuditLogMapper;
import com.yundao.bp.sys.service.AuditService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

/**
 * 审计日志实现。
 *
 * <p>写审计用 {@code REQUIRES_NEW}：即使主业务回滚，审计也要留痕
 * （例如操作失败本身也需要记录）。
 */
@Service
public class AuditServiceImpl implements AuditService {

    private final SysAuditLogMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public AuditServiceImpl(SysAuditLogMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public void record(String auditType, String auditLevel, String bizType, Long bizId,
                       Long operatorId, String operatorName,
                       String targetType, String targetId, String action,
                       String beforeJson, String afterJson, String reason, String clientIp) {
        LocalDateTime now = LocalDateTime.now();
        SysAuditLog e = new SysAuditLog();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setAuditType(auditType == null ? "OTHER" : auditType);
        e.setAuditLevel(auditLevel == null ? "NORMAL" : auditLevel);
        e.setBizType(bizType);
        e.setBizId(bizId);
        e.setOperatorId(operatorId);
        e.setOperatorName(operatorName);
        e.setTargetType(targetType);
        e.setTargetId(targetId);
        e.setAction(action);
        e.setBeforeJson(beforeJson);
        e.setAfterJson(afterJson);
        e.setReason(reason);
        e.setClientIp(clientIp);
        e.setAuditTime(now);
        e.setCreateTime(now);
        mapper.insert(e);
    }

    @Override
    public PageResult<SysAuditLog> page(long pageNum, long pageSize, String auditType,
                                        String level, String operatorName, LocalDate dateFrom,
                                        LocalDate dateTo) {
        LambdaQueryWrapper<SysAuditLog> qw = new LambdaQueryWrapper<SysAuditLog>()
                .eq(auditType != null && !auditType.isBlank(),
                        SysAuditLog::getAuditType, auditType)
                .eq(level != null && !level.isBlank(), SysAuditLog::getAuditLevel, level)
                .like(operatorName != null && !operatorName.isBlank(),
                        SysAuditLog::getOperatorName, operatorName)
                .orderByDesc(SysAuditLog::getId);
        if (dateFrom != null) {
            qw.ge(SysAuditLog::getAuditTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(SysAuditLog::getAuditTime, dateTo.plusDays(1).atStartOfDay());
        }
        IPage<SysAuditLog> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<SysAuditLog> rows = page.getRecords();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public SysAuditLog get(Long id) {
        SysAuditLog e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("审计日志");
        }
        return e;
    }
}
'''

# ==================== DictService ====================
F['sys/service/DictService.java'] = '''package com.yundao.bp.sys.service;

import com.yundao.bp.sys.entity.SysDict;
import java.util.List;
import java.util.Map;

/**
 * 数据字典服务。
 *
 * <p>租户级优先：同 `dict_type + dict_code` 时，本租户配置覆盖系统内置。
 */
public interface DictService {

    /** 按类型取字典项（租户优先，已排序）。 */
    List<SysDict> listByType(String dictType);

    /** 按类型取「编码 → 标签」映射（前端下拉用）。 */
    Map<String, String> mapByType(String dictType);

    /** 取某类型某编码的标签。 */
    String label(String dictType, String dictCode);

    /** 全部字典类型列表。 */
    List<String> types();

    /** 新增字典项。 */
    SysDict create(String dictType, String dictCode, String dictLabel, String dictValue,
                   Integer sortNo, String remark);

    /** 启用/停用。 */
    SysDict setStatus(Long id, boolean enabled);
}
'''

F['sys/service/impl/DictServiceImpl.java'] = '''package com.yundao.bp.sys.service.impl;

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
        List<SysDict> all = mapper.selectList(new LambdaQueryWrapper<SysDict>()
                .eq(SysDict::getDictType, dictType)
                .eq(SysDict::getDictStatus, "ENABLED")
                .orderByAsc(SysDict::getSortNo)
                .orderByAsc(SysDict::getId));
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
        List<SysDict> all = mapper.selectList(new LambdaQueryWrapper<SysDict>()
                .select(SysDict::getDictType)
                .eq(SysDict::getDictStatus, "ENABLED"));
        LinkedHashSet<String> set = new LinkedHashSet<>();
        all.forEach(d -> set.add(d.getDictType()));
        return new ArrayList<>(set);
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
'''

# ==================== ConfigService ====================
F['sys/service/ConfigService.java'] = '''package com.yundao.bp.sys.service;

import com.yundao.bp.sys.entity.SysConfig;
import java.math.BigDecimal;
import java.util.List;

/**
 * 系统参数服务。
 *
 * <p>⭐ <b>核心用途</b>：把政策参数从硬编码改为可配置，支持分地区差异。
 * 优先级：<b>本租户配置 &gt; 全局配置 &gt; 调用方默认值</b>。
 */
public interface ConfigService {

    /** 取字符串参数。 */
    String getString(String key, String defaultValue);

    /** 取整型参数。 */
    int getInt(String key, int defaultValue);

    /** 取小数值。 */
    BigDecimal getDecimal(String key, BigDecimal defaultValue);

    /** 取布尔参数。 */
    boolean getBool(String key, boolean defaultValue);

    /** 按分组列出全部参数。 */
    List<SysConfig> listByGroup(String group);

    /** 全部参数。 */
    List<SysConfig> listAll();

    /** 设置参数（不存在则创建）。 */
    SysConfig set(String key, String value, String description);
}
'''

F['sys/service/impl/ConfigServiceImpl.java'] = '''package com.yundao.bp.sys.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.sys.entity.SysConfig;
import com.yundao.bp.sys.mapper.SysConfigMapper;
import com.yundao.bp.sys.service.ConfigService;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 系统参数实现。
 *
 * <p>读取优先级：本租户 &gt; 全局（tenant_id 为空） &gt; 默认值。
 * 读取失败一律回退默认值，<b>不让参数缺失导致业务中断</b>。
 */
@Service
public class ConfigServiceImpl implements ConfigService {

    private static final Logger log = LoggerFactory.getLogger(ConfigServiceImpl.class);

    private final SysConfigMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public ConfigServiceImpl(SysConfigMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    public String getString(String key, String defaultValue) {
        SysConfig c = find(key);
        if (c == null || c.getConfigValue() == null || c.getConfigValue().isBlank()) {
            return defaultValue;
        }
        return c.getConfigValue();
    }

    @Override
    public int getInt(String key, int defaultValue) {
        try {
            return Integer.parseInt(getString(key, String.valueOf(defaultValue)).trim());
        } catch (Exception e) {
            log.warn("参数 {} 非整型，回退默认值 {}", key, defaultValue);
            return defaultValue;
        }
    }

    @Override
    public BigDecimal getDecimal(String key, BigDecimal defaultValue) {
        try {
            return new BigDecimal(getString(key, String.valueOf(defaultValue)).trim());
        } catch (Exception e) {
            log.warn("参数 {} 非数值，回退默认值 {}", key, defaultValue);
            return defaultValue;
        }
    }

    @Override
    public boolean getBool(String key, boolean defaultValue) {
        String v = getString(key, String.valueOf(defaultValue)).trim();
        return "true".equalsIgnoreCase(v) || "1".equals(v) || "Y".equalsIgnoreCase(v);
    }

    @Override
    public List<SysConfig> listByGroup(String group) {
        return mapper.selectList(new LambdaQueryWrapper<SysConfig>()
                .eq(group != null && !group.isBlank(), SysConfig::getConfigGroup, group)
                .orderByAsc(SysConfig::getConfigKey));
    }

    @Override
    public List<SysConfig> listAll() {
        return mapper.selectList(new LambdaQueryWrapper<SysConfig>()
                .orderByAsc(SysConfig::getConfigKey));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public SysConfig set(String key, String value, String description) {
        String tenant = TenantContext.get() == null ? null : TenantContext.tenantId();
        SysConfig c = mapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                .eq(SysConfig::getTenantId, tenant)
                .eq(SysConfig::getConfigKey, key)
                .last("LIMIT 1"));
        LocalDateTime now = LocalDateTime.now();
        if (c == null) {
            c = new SysConfig();
            c.setId(idGen.nextId());
            c.setTenantId(tenant);
            c.setConfigKey(key);
            c.setConfigValue(value);
            c.setConfigGroup("BUSINESS");
            c.setValueType(guessType(value));
            c.setIsEncrypted(0);
            c.setIsSystem(0);
            c.setDescription(description);
            c.setCreateTime(now);
            c.setUpdateTime(now);
            mapper.insert(c);
        } else {
            c.setConfigValue(value);
            if (description != null) {
                c.setDescription(description);
            }
            c.setUpdateTime(now);
            mapper.updateById(c);
        }
        log.info("参数设置：{} = {}（租户 {}）", key, value, tenant);
        return c;
    }

    /** 查找：本租户优先，其次全局。 */
    private SysConfig find(String key) {
        String tenant = null;
        try {
            tenant = TenantContext.get() == null ? null : TenantContext.tenantId();
        } catch (Exception ignored) {
            // 无租户上下文时只查全局
        }
        if (tenant != null) {
            SysConfig own = mapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                    .eq(SysConfig::getTenantId, tenant)
                    .eq(SysConfig::getConfigKey, key)
                    .last("LIMIT 1"));
            if (own != null) {
                return own;
            }
        }
        return mapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                .isNull(SysConfig::getTenantId)
                .eq(SysConfig::getConfigKey, key)
                .last("LIMIT 1"));
    }

    private static String guessType(String v) {
        if (v == null) {
            return "STRING";
        }
        if (v.matches("^-?\\\\d+$")) {
            return "INT";
        }
        if (v.matches("^-?\\\\d+\\\\.\\\\d+$")) {
            return "DECIMAL";
        }
        if ("true".equalsIgnoreCase(v) || "false".equalsIgnoreCase(v)) {
            return "BOOL";
        }
        return "STRING";
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
