# -*- coding: utf-8 -*-
"""生成合同变更模块（常量 + 实体 + DTO）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/constant/ChangeType.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 合同变更类型（对应 {@code bp_biz_contract_change.change_type}）。
 */
public enum ChangeType {

    RENEW("续签"),
    RENT_ADJUST("租金调整"),
    PERIOD("租期变更"),
    LESSEE("承租人变更"),
    OTHER("其他");

    private final String label;

    ChangeType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否影响租金（需同步账单/计费）。 */
    public boolean affectsRent() {
        return this == RENT_ADJUST || this == RENEW;
    }
}
'''

FILES['biz/constant/ApproveStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 变更审批状态（对应 {@code bp_biz_contract_change.approve_status}）。
 *
 * <pre>
 *   PENDING 待审批 ──批准──> APPROVED 已批准（生效，写回合同） ──终态
 *        └──驳回──> REJECTED 已驳回（终态）
 * </pre>
 */
public enum ApproveStatus {

    PENDING("待审批"),
    APPROVED("已批准"),
    REJECTED("已驳回");

    private final String label;

    ApproveStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == APPROVED || this == REJECTED;
    }

    public static Set<ApproveStatus> nextOf(ApproveStatus from) {
        return switch (from) {
            case PENDING -> Set.of(APPROVED, REJECTED);
            case APPROVED, REJECTED -> Set.of();
        };
    }
}
'''

FILES['biz/entity/BizContractChange.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 合同变更。对应 {@code bp_biz_contract_change}。
 *
 * <p>{@code before_json} / {@code after_json} 保存变更前后关键字段，
 * 保证任何调价都可追溯、可审计。
 */
@Data
@TableName("bp_biz_contract_change")
public class BizContractChange {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long contractId;
    private Long newContractId;

    /** RENEW / RENT_ADJUST / PERIOD / LESSEE / OTHER */
    private String changeType;
    private String changeReason;

    /** 变更前关键字段 JSON */
    private String beforeJson;
    /** 变更后关键字段 JSON */
    private String afterJson;

    /** PENDING / APPROVED / REJECTED */
    private String approveStatus;
    private LocalDate effectiveDate;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['biz/mapper/BizContractChangeMapper.java'] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.BizContractChange;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizContractChangeMapper extends BaseMapper<BizContractChange> {
}
'''

FILES['biz/dto/ChangeCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 发起合同变更。
 *
 * <p>按 {@code changeType} 填对应字段：
 * <ul>
 *   <li>{@code RENT_ADJUST} → {@code newMonthlyRent}</li>
 *   <li>{@code PERIOD} → {@code newLeaseEnd}</li>
 *   <li>{@code OTHER} → {@code remark}</li>
 * </ul>
 */
public record ChangeCreateCmd(

        @NotBlank(message = "变更类型不能为空")
        @Pattern(regexp = "RENEW|RENT_ADJUST|PERIOD|LESSEE|OTHER", message = "变更类型不合法")
        String changeType,

        String changeReason,

        /** 新月租金（RENT_ADJUST / RENEW） */
        BigDecimal newMonthlyRent,

        /** 新止租日（PERIOD / RENEW） */
        LocalDate newLeaseEnd,

        /** 新承租人人员ID（LESSEE） */
        Long newLesseePersonId,
        String newLesseeName,

        /** 生效日期；为空则批准时取当天 */
        LocalDate effectiveDate,

        /** 其他变更说明 */
        String remark
) {
}
'''

FILES['biz/dto/ChangeVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ApproveStatus;
import com.yundao.bp.biz.constant.ChangeType;
import com.yundao.bp.biz.entity.BizContractChange;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 合同变更视图。
 */
public record ChangeVO(
        Long id,
        Long contractId,
        Long newContractId,
        String changeType,
        String changeTypeLabel,
        String changeReason,
        String beforeJson,
        String afterJson,
        String approveStatus,
        String approveStatusLabel,
        LocalDate effectiveDate,
        LocalDateTime createTime
) {
    public static ChangeVO from(BizContractChange e) {
        if (e == null) {
            return null;
        }
        ChangeType ct;
        try {
            ct = ChangeType.valueOf(e.getChangeType());
        } catch (IllegalArgumentException ex) {
            ct = ChangeType.OTHER;
        }
        ApproveStatus st;
        try {
            st = ApproveStatus.valueOf(e.getApproveStatus());
        } catch (IllegalArgumentException ex) {
            st = ApproveStatus.PENDING;
        }
        return new ChangeVO(e.getId(), e.getContractId(), e.getNewContractId(),
                e.getChangeType(), ct.label(), e.getChangeReason(), e.getBeforeJson(),
                e.getAfterJson(), e.getApproveStatus(), st.label(), e.getEffectiveDate(),
                e.getCreateTime());
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
