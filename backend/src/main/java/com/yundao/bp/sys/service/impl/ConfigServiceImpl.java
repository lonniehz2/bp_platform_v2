package com.yundao.bp.sys.service.impl;

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
        if (c == null) {
            // 兼容历史：先有全局默认行（tenant_id 为空），再改时就更新它，不再插一条
            c = mapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                    .and(w -> w.isNull(SysConfig::getTenantId)
                            .or().eq(SysConfig::getTenantId, ""))
                    .eq(SysConfig::getConfigKey, key)
                    .last("LIMIT 1"));
        }
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
        if (v.matches("^-?\\d+$")) {
            return "INT";
        }
        if (v.matches("^-?\\d+\\.\\d+$")) {
            return "DECIMAL";
        }
        if ("true".equalsIgnoreCase(v) || "false".equalsIgnoreCase(v)) {
            return "BOOL";
        }
        return "STRING";
    }
}
