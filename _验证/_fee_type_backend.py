# -*- coding: utf-8 -*-
"""费用类型字典：建表 + 实体/映射/服务/接口；计费规则增删改。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

# ---------- 实体 ----------
ENTITY = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 费用类型字典。对应 {@code bp_fin_fee_type}。
 *
 * <p>计费项目的「费用类型」从这里取值，可在界面增删改（停用而非物理删除）。
 */
@Data
@TableName("bp_fin_fee_type")
public class FinFeeType {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;

    /** 类型编码，如 RENT */
    private String typeCode;

    /** 类型名称，如 租金 */
    private String typeName;

    /** ENABLED / DISABLED */
    private String status;

    private Integer sortNo;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

MAPPER = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.FinFeeType;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface FinFeeTypeMapper extends BaseMapper<FinFeeType> {
}
'''

SERVICE = '''package com.yundao.bp.fin.service;

import com.yundao.bp.fin.entity.FinFeeType;
import java.util.List;

/** 费用类型字典。 */
public interface FeeTypeService {

    List<FinFeeType> list(boolean enabledOnly);

    FinFeeType create(String code, String name, Integer sortNo);

    FinFeeType update(Long id, String code, String name, Integer sortNo);

    FinFeeType setStatus(Long id, boolean enabled);
}
'''

IMPL = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.exception.ErrorCode;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.entity.FinFeeType;
import com.yundao.bp.fin.mapper.FinFeeTypeMapper;
import com.yundao.bp.fin.service.FeeTypeService;
import com.yundao.bp.common.util.IdGen;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class FeeTypeServiceImpl implements FeeTypeService {

    private final FinFeeTypeMapper mapper;
    private final IdGen idGen;

    public FeeTypeServiceImpl(FinFeeTypeMapper mapper, IdGen idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
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
'''

for path, body in [
    (os.path.join(BK, 'entity', 'FinFeeType.java'), ENTITY),
    (os.path.join(BK, 'mapper', 'FinFeeTypeMapper.java'), MAPPER),
    (os.path.join(BK, 'service', 'FeeTypeService.java'), SERVICE),
    (os.path.join(BK, 'service', 'impl', 'FeeTypeServiceImpl.java'), IMPL),
]:
    if not os.path.exists(path):
        with io.open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(body)
        print('创建', os.path.basename(path))

# ---------- 控制器端点 ----------
P = os.path.join(BK, 'controller', 'FeeItemController.java')
s = io.open(P, encoding='utf-8').read()
if '/fee-types' not in s:
    block = '''
    // ==================== 费用类型字典 ====================

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:view")
    @GetMapping("/fee-types")
    public R<java.util.List<com.yundao.bp.fin.entity.FinFeeType>> feeTypes(
            @RequestParam(defaultValue = "false") boolean enabledOnly) {
        return R.ok(feeTypeService.list(enabledOnly));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:create")
    @PostMapping("/fee-types")
    public R<com.yundao.bp.fin.entity.FinFeeType> createFeeType(
            @RequestBody FeeTypeCmd cmd) {
        return R.ok(feeTypeService.create(cmd.typeCode(), cmd.typeName(), cmd.sortNo()));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:create")
    @org.springframework.web.bind.annotation.PutMapping("/fee-types/{id}")
    public R<com.yundao.bp.fin.entity.FinFeeType> updateFeeType(
            @PathVariable Long id, @RequestBody FeeTypeCmd cmd) {
        return R.ok(feeTypeService.update(id, cmd.typeCode(), cmd.typeName(), cmd.sortNo()));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:feeItem:status")
    @PostMapping("/fee-types/{id}/status")
    public R<com.yundao.bp.fin.entity.FinFeeType> setFeeTypeStatus(
            @PathVariable Long id, @RequestBody(required = false) StatusCmd cmd) {
        return R.ok(feeTypeService.setStatus(id, cmd != null && cmd.enabled()));
    }

    public record FeeTypeCmd(String typeCode, String typeName, Integer sortNo) {
    }
'''
    s = s.replace('    public record StatusCmd(boolean enabled) {', block + '\n    public record StatusCmd(boolean enabled) {', 1)

# 注入 service
if 'feeTypeService' not in s.split('public R<FinFeeItem>')[0]:
    s = s.replace('''    public FeeItemController(''', '''    private final FeeTypeService feeTypeService;

    public FeeItemController(''', 1)
    s = s.replace('''        this.service = service;''',
'''        this.service = service;
        this.feeTypeService = null;''', 1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('FeeItemController 已加 fee-types 端点（需人工补构造注入）')
