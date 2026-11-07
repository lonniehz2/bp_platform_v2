package com.yundao.bp.property.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.property.entity.PropCategory;
import com.yundao.bp.property.mapper.PropCategoryMapper;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Locale;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 物业收入/支出分类：系统分类只读，租户仅能在允许扩展的父级下新增叶子。 */
@Service
public class PropertyCategoryService {

    private final PropCategoryMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public PropertyCategoryService(PropCategoryMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    public List<PropCategory> list(String type) {
        String t = normalizeType(type);
        return mapper.selectList(new LambdaQueryWrapper<PropCategory>()
                .eq(PropCategory::getTenantId, TenantContext.tenantId())
                .eq(t != null, PropCategory::getCategoryType, t)
                .orderByAsc(PropCategory::getCategoryType)
                .orderByAsc(PropCategory::getSortNo)
                .orderByAsc(PropCategory::getId));
    }

    @Transactional(rollbackFor = Exception.class)
    public PropCategory create(CreateCmd cmd) {
        String type = normalizeType(cmd.categoryType());
        if (type == null) {
            throw BizException.paramInvalid("分类类型不能为空");
        }
        if (cmd.parentId() == null) {
            throw BizException.paramInvalid("只能在一级分类下新增二级分类");
        }
        PropCategory parent = mapper.selectById(cmd.parentId());
        if (parent == null || !type.equals(parent.getCategoryType())) {
            throw BizException.notFound("父级分类");
        }
        if (parent.getAllowCustom() == null || parent.getAllowCustom() != 1) {
            throw BizException.stateConflict("该分类不允许新增下级");
        }
        String code = cmd.categoryCode() == null ? "" : cmd.categoryCode().trim().toUpperCase(Locale.ROOT);
        if (!code.matches("[A-Z0-9_]{2,64}")) {
            throw BizException.paramInvalid("分类编码只能包含大写字母、数字和下划线");
        }
        Long dup = mapper.selectCount(new LambdaQueryWrapper<PropCategory>()
                .eq(PropCategory::getTenantId, TenantContext.tenantId())
                .eq(PropCategory::getCategoryType, type)
                .eq(PropCategory::getCategoryCode, code));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("分类编码已存在");
        }
        if (cmd.categoryName() == null || cmd.categoryName().isBlank()) {
            throw BizException.paramInvalid("分类名称不能为空");
        }
        PropCategory e = new PropCategory();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setCategoryType(type);
        e.setParentId(parent.getId());
        e.setCategoryCode(code);
        e.setCategoryName(cmd.categoryName().trim());
        e.setCategoryLevel((parent.getCategoryLevel() == null ? 1 : parent.getCategoryLevel()) + 1);
        e.setIsSystem(0);
        e.setIsLeaf(1);
        e.setAllowCustom(0);
        e.setReportLineCode(parent.getReportLineCode());
        e.setStatus("ENABLED");
        e.setSortNo(cmd.sortNo() == null ? 0 : cmd.sortNo());
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        e.setCreateBy(String.valueOf(TenantContext.userId()));
        e.setCreateTime(LocalDateTime.now());
        e.setUpdateBy(String.valueOf(TenantContext.userId()));
        e.setUpdateTime(LocalDateTime.now());
        mapper.insert(e);
        return e;
    }

    @Transactional(rollbackFor = Exception.class)
    public PropCategory update(Long id, UpdateCmd cmd) {
        PropCategory e = require(id);
        if (cmd.categoryName() != null && !cmd.categoryName().isBlank()) {
            e.setCategoryName(cmd.categoryName().trim());
        }
        if (cmd.sortNo() != null) {
            e.setSortNo(cmd.sortNo());
        }
        if (cmd.status() != null && !cmd.status().isBlank()) {
            if (!List.of("ENABLED", "DISABLED").contains(cmd.status())) {
                throw BizException.paramInvalid("分类状态不合法");
            }
            e.setStatus(cmd.status());
        }
        if (cmd.remark() != null) {
            e.setRemark(cmd.remark());
        }
        e.setUpdateBy(String.valueOf(TenantContext.userId()));
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return e;
    }

    @Transactional(rollbackFor = Exception.class)
    public void delete(Long id) {
        PropCategory e = require(id);
        if (e.getIsSystem() != null && e.getIsSystem() == 1) {
            throw BizException.stateConflict("系统预置分类不能删除，可停用");
        }
        Long children = mapper.selectCount(new LambdaQueryWrapper<PropCategory>()
                .eq(PropCategory::getTenantId, TenantContext.tenantId())
                .eq(PropCategory::getParentId, id));
        if (children != null && children > 0) {
            throw BizException.stateConflict("存在下级分类，不能删除");
        }
        // 试用期尚未产生账单；V1 账单表落地后在此增加“已被账单/支出使用”的校验。
        mapper.deleteById(id);
    }

    private PropCategory require(Long id) {
        PropCategory e = mapper.selectById(id);
        if (e == null || !TenantContext.tenantId().equals(e.getTenantId())) {
            throw BizException.notFound("分类");
        }
        return e;
    }

    private static String normalizeType(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        String t = value.trim().toUpperCase(Locale.ROOT);
        if (!List.of("INCOME", "EXPENSE").contains(t)) {
            throw BizException.paramInvalid("分类类型只能是 INCOME 或 EXPENSE");
        }
        return t;
    }

    public record CreateCmd(String categoryType, Long parentId, String categoryCode,
                            String categoryName, Integer sortNo, String remark) {
    }

    public record UpdateCmd(String categoryName, Integer sortNo, String status, String remark) {
    }
}
