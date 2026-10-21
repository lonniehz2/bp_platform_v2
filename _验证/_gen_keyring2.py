# -*- coding: utf-8 -*-
"""生成钥匙包 + 授权对账 服务与接口"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

F['grant/service/KeyringService.java'] = '''package com.yundao.bp.grant.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.grant.dto.KeyringVO;
import com.yundao.bp.grant.entity.GrantKeyring;
import java.util.List;

/**
 * 钥匙包服务。
 *
 * <p><b>以人为中心管理多介质</b>：一个人可有多把钥匙（人脸/指纹/掌静脉/密码/卡），
 * 按<b>四分类</b>区分安全等级。这是 ★ 级「四级权限」考核的直接落点。
 */
public interface KeyringService {

    /**
     * 新增钥匙。
     *
     * <p>校验：同一人员同类型同别名不可重复；非实名介质必须设有效期。
     */
    KeyringVO add(KeyringCmd cmd);

    /** 某人的钥匙包（含分类统计）。 */
    List<KeyringVO> listByPerson(Long personId);

    /** 一个人的钥匙包概览（四分类各几把、是否满足强安全要求）。 */
    java.util.Map<String, Object> summary(Long personId);

    /** 冻结/解冻。 */
    KeyringVO setStatus(Long id, String status);

    /** 逻辑删除。 */
    KeyringVO remove(Long id);

    PageResult<KeyringVO> page(long pageNum, long pageSize, Long personId, String keyType,
                               String keyClass, String keyStatus);

    GrantKeyring get(Long id);

    /** 新增钥匙入参。 */
    record KeyringCmd(Long personId, String keyType, String keyAlias, String channelValue,
                      String keySource, String verifyWay, String syncScope,
                      String expireTime) {
    }
}
'''

F['grant/service/impl/KeyringServiceImpl.java'] = '''package com.yundao.bp.grant.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.grant.constant.KeyClass;
import com.yundao.bp.grant.constant.KeyType;
import com.yundao.bp.grant.dto.KeyringVO;
import com.yundao.bp.grant.entity.GrantKeyring;
import com.yundao.bp.grant.mapper.GrantKeyringMapper;
import com.yundao.bp.grant.service.KeyringService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 钥匙包实现。
 */
@Service
public class KeyringServiceImpl implements KeyringService {

    private static final Logger log = LoggerFactory.getLogger(KeyringServiceImpl.class);

    private final GrantKeyringMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public KeyringServiceImpl(GrantKeyringMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KeyringVO add(KeyringCmd cmd) {
        if (cmd.personId() == null) {
            throw BizException.paramInvalid("所属人员不能为空");
        }
        KeyType type = KeyType.of(cmd.keyType());
        if (type == null) {
            throw BizException.paramInvalid("非法钥匙类型：" + cmd.keyType());
        }
        if (cmd.channelValue() == null || cmd.channelValue().isBlank()) {
            throw BizException.paramInvalid("介质值不能为空");
        }
        KeyClass cls = KeyClass.derive(type, cmd.verifyWay(),
                cmd.keySource() == null ? "ADMIN" : cmd.keySource());

        LocalDateTime expire = null;
        if (cmd.expireTime() != null && !cmd.expireTime().isBlank()) {
            try {
                expire = LocalDateTime.parse(cmd.expireTime().replace(' ', 'T'));
            } catch (Exception e) {
                throw BizException.paramInvalid("有效期格式应为 yyyy-MM-dd HH:mm:ss");
            }
            if (expire.isBefore(LocalDateTime.now())) {
                throw BizException.paramInvalid("有效期不能早于当前时间");
            }
        }
        // 弱安全介质必须限期，避免长期有效的弱凭证
        if (cls.requireExpireTime() && expire == null) {
            throw BizException.paramInvalid(
                    "「" + cls.label() + "」属弱安全介质，必须设置有效期");
        }

        // 同一人员同类型同别名不可重复（避免刷重复人脸/指纹）
        Long dup = mapper.selectCount(new LambdaQueryWrapper<GrantKeyring>()
                .eq(GrantKeyring::getPersonId, cmd.personId())
                .eq(GrantKeyring::getKeyType, cmd.keyType())
                .eq(cmd.keyAlias() != null && !cmd.keyAlias().isBlank(),
                        GrantKeyring::getKeyAlias, cmd.keyAlias())
                .ne(GrantKeyring::getKeyStatus, "DELETED"));
        if (dup != null && dup > 0) {
            throw new BizException(ErrorCode.DUPLICATED,
                    "该人员已存在同类型同别名的钥匙（" + type.label() + "）");
        }

        LocalDateTime now = LocalDateTime.now();
        GrantKeyring e = new GrantKeyring();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setPersonId(cmd.personId());
        e.setKeyType(type.name());
        e.setKeyClass(cls.name());
        e.setKeyAlias(cmd.keyAlias());
        e.setChannelModuleType(type.moduleType());
        e.setChannelType(type.channelType());
        e.setChannelValue(cmd.channelValue());
        e.setKeySource(cmd.keySource() == null ? "ADMIN" : cmd.keySource());
        e.setVerifyWay(cmd.verifyWay());
        e.setIsReal(cls.realName() ? 1 : 0);
        e.setSyncScope(cmd.syncScope() == null ? "ALL_GRANTED" : cmd.syncScope());
        e.setKeyStatus("ACTIVE");
        e.setExpireTime(expire);
        e.setIsDeleted(0);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        log.info("钥匙入包：人员 {} 新增 {}（{}），分类 {}",
                cmd.personId(), type.name(), type.label(), cls.label());
        return KeyringVO.from(e);
    }

    @Override
    public List<KeyringVO> listByPerson(Long personId) {
        if (personId == null) {
            throw BizException.paramInvalid("人员ID不能为空");
        }
        return mapper.selectList(new LambdaQueryWrapper<GrantKeyring>()
                        .eq(GrantKeyring::getPersonId, personId)
                        .ne(GrantKeyring::getKeyStatus, "DELETED")
                        .orderByAsc(GrantKeyring::getId))
                .stream().map(KeyringVO::from).toList();
    }

    @Override
    public Map<String, Object> summary(Long personId) {
        List<KeyringVO> list = listByPerson(personId);
        Map<String, Integer> byClass = new LinkedHashMap<>();
        for (KeyClass c : KeyClass.values()) {
            byClass.put(c.name(), 0);
        }
        int active = 0;
        int real = 0;
        for (KeyringVO k : list) {
            if ("ACTIVE".equals(k.keyStatus())) {
                active++;
                byClass.merge(k.keyClass(), 1, Integer::sum);
                if (Boolean.TRUE.equals(k.real())) {
                    real++;
                }
            }
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("personId", personId);
        m.put("total", list.size());
        m.put("active", active);
        m.put("realCount", real);
        m.put("weakCount", active - real);
        m.put("byClass", byClass);
        // 强安全要求：至少 1 把实名介质
        m.put("meetsStrongSecurity", real >= 1);
        m.put("advice", real >= 1 ? "已具备实名介质，可开放大门权限"
                : "仅有弱安全介质，不可开放大门权限，建议补录人脸或指纹");
        return m;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KeyringVO setStatus(Long id, String status) {
        GrantKeyring e = require(id);
        if (!List.of("ACTIVE", "FROZEN", "EXPIRED").contains(status)) {
            throw BizException.paramInvalid("非法状态：" + status);
        }
        if ("DELETED".equals(e.getKeyStatus())) {
            throw BizException.stateConflict("已删除的钥匙不可变更状态");
        }
        e.setKeyStatus(status);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("钥匙状态变更：{} → {}", id, status);
        return KeyringVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public KeyringVO remove(Long id) {
        GrantKeyring e = require(id);
        e.setKeyStatus("DELETED");
        e.setIsDeleted(1);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("钥匙已删除：{}", id);
        return KeyringVO.from(e);
    }

    @Override
    public PageResult<KeyringVO> page(long pageNum, long pageSize, Long personId,
                                      String keyType, String keyClass, String keyStatus) {
        LambdaQueryWrapper<GrantKeyring> qw = new LambdaQueryWrapper<GrantKeyring>()
                .eq(personId != null, GrantKeyring::getPersonId, personId)
                .eq(keyType != null && !keyType.isBlank(), GrantKeyring::getKeyType, keyType)
                .eq(keyClass != null && !keyClass.isBlank(),
                        GrantKeyring::getKeyClass, keyClass)
                .eq(keyStatus != null && !keyStatus.isBlank(),
                        GrantKeyring::getKeyStatus, keyStatus)
                .orderByDesc(GrantKeyring::getId);
        IPage<GrantKeyring> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<KeyringVO> rows = new ArrayList<>();
        for (GrantKeyring e : page.getRecords()) {
            rows.add(KeyringVO.from(e));
        }
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public GrantKeyring get(Long id) {
        return require(id);
    }

    private GrantKeyring require(Long id) {
        GrantKeyring e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("钥匙");
        }
        return e;
    }
}
'''

F['grant/dto/KeyringVO.java'] = '''package com.yundao.bp.grant.dto;

import com.yundao.bp.grant.constant.KeyClass;
import com.yundao.bp.grant.constant.KeyType;
import com.yundao.bp.grant.entity.GrantKeyring;
import java.time.LocalDateTime;

/**
 * 钥匙视图（<b>不回显介质值</b>，避免人脸/指纹/密码泄露）。
 */
public record KeyringVO(
        Long id,
        Long personId,
        String keyType,
        String keyTypeLabel,
        String keyClass,
        String keyClassLabel,
        String keyAlias,
        String channelType,
        String keySource,
        String verifyWay,
        Boolean real,
        String syncScope,
        String keyStatus,
        LocalDateTime expireTime,
        LocalDateTime createTime
) {
    public static KeyringVO from(GrantKeyring e) {
        if (e == null) {
            return null;
        }
        KeyType t = KeyType.of(e.getKeyType());
        KeyClass c = KeyClass.of(e.getKeyClass());
        return new KeyringVO(e.getId(), e.getPersonId(), e.getKeyType(),
                t == null ? e.getKeyType() : t.label(), e.getKeyClass(),
                c == null ? e.getKeyClass() : c.label(), e.getKeyAlias(),
                e.getChannelType(), e.getKeySource(), e.getVerifyWay(),
                e.getIsReal() != null && e.getIsReal() == 1, e.getSyncScope(),
                e.getKeyStatus(), e.getExpireTime(), e.getCreateTime());
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
