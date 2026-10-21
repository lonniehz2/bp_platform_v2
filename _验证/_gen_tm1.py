# -*- coding: utf-8 -*-
"""生成 biz 退租腾退模块"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/constant/TerminationStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 退租单状态机（对应 {@code bp_biz_termination.termination_status}）。
 *
 * <pre>
 *   APPLYING 申请中 ──提交审批──> APPROVING 审批中 ──批准──> APPROVED 已批准
 *                                      │                      │
 *                                   驳回                    办结（验房+结算+释放房源+回收授权）
 *                                      ↓                      ↓
 *                                REJECTED（终态）        COMPLETED（终态）
 *   APPLYING ──撤单──> CANCELLED（终态）
 * </pre>
 *
 * <p><b>COMPLETED 的四个前置</b>（缺一不可）：
 * 验房完成、结算完成、房源已释放、授权已回收。
 */
public enum TerminationStatus {

    APPLYING("申请中", false),
    APPROVING("审批中", false),
    APPROVED("已批准", false),
    REJECTED("已驳回", true),
    COMPLETED("已完成", true),
    CANCELLED("已取消", true);

    private final String label;
    private final boolean terminal;

    TerminationStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    public static Set<TerminationStatus> nextOf(TerminationStatus from) {
        return switch (from) {
            case APPLYING -> Set.of(APPROVING, CANCELLED);
            case APPROVING -> Set.of(APPROVED, REJECTED);
            case APPROVED -> Set.of(COMPLETED);
            case REJECTED, COMPLETED, CANCELLED -> Set.of();
        };
    }
}
'''

FILES['biz/constant/TerminationType.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 退租类型（对应 {@code bp_biz_termination.termination_type}）。
 *
 * <p>不同类型决定政策口径：
 * {@code EXPEL 违规清退} 需写 {@code ban_reapply_end_date}（如 5 年内不得再申请）。
 */
public enum TerminationType {

    NORMAL("正常退租"),
    EXPEL("违规清退"),
    EXPIRE("到期不续"),
    EXCHANGE("换房退出"),
    OTHER("其他");

    private final String label;

    TerminationType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['biz/constant/SettleStatus.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 结算状态（对应 {@code bp_biz_termination.settle_status}）。
 */
public enum SettleStatus {

    PENDING("待结算"),
    SETTLED("已结算"),
    WAIVED("已免除");

    private final String label;

    SettleStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['biz/entity/BizTermination.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 退租/腾退单。对应 {@code bp_biz_termination}。
 */
@Data
@TableName("bp_biz_termination")
public class BizTermination {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String terminationNo;

    private Long contractId;
    private Long houseId;
    private Long personId;

    /** NORMAL / EXPEL / EXPIRE / EXCHANGE / OTHER */
    private String terminationType;

    private LocalDateTime applyTime;
    private LocalDate planExitDate;
    private LocalDate actualExitDate;
    private String exitReason;

    /** PENDING / PASSED / ABNORMAL */
    private String inspectStatus;
    private String inspectResult;
    private String inspectImages;

    private BigDecimal damageAmount;
    /** 结算金额（正数退还，负数补缴） */
    private BigDecimal settleAmount;
    private BigDecimal depositRefund;
    private BigDecimal arrearsAmount;

    /** PENDING / SETTLED / WAIVED */
    private String settleStatus;

    /** APPLYING / APPROVING / APPROVED / REJECTED / COMPLETED / CANCELLED */
    private String terminationStatus;

    private Integer houseReleased;
    private Integer grantRevoked;

    /** 重庆：腾退过渡期 */
    private LocalDate transitionStartDate;
    private LocalDate transitionEndDate;
    private Integer transitionMonths;
    /** 重庆：期内 1.5，期满 2.0 */
    private BigDecimal transitionRentMultiplier;

    /** 成都：搬迁期（不超过 6 个月） */
    private LocalDate relocationStartDate;
    private LocalDate relocationEndDate;

    private Integer enforceFlag;
    private LocalDate enforceApplyDate;
    private String enforceCourt;
    private String enforceResult;

    /** 成都：承租人可指定物品处置人 */
    private String itemHandlerName;
    private String itemHandlerPhone;
    private Integer notaryFlag;
    private String notaryNo;

    /** 违规退回：限制再申请结束日 */
    private LocalDate banReapplyEndDate;

    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['biz/mapper/BizTerminationMapper.java'] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.BizTermination;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizTerminationMapper extends BaseMapper<BizTermination> {
}
'''

FILES['biz/dto/TerminationCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDate;

/**
 * 申请退租。
 */
public record TerminationCreateCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        @NotNull(message = "房源不能为空")
        Long houseId,

        Long personId,

        @NotBlank(message = "退租类型不能为空")
        @Pattern(regexp = "NORMAL|EXPEL|EXPIRE|EXCHANGE|OTHER", message = "退租类型不合法")
        String terminationType,

        LocalDate planExitDate,
        String exitReason,

        /** 重庆：过渡期月数（腾退给 3 个月） */
        Integer transitionMonths,
        /** 过渡期租金倍率（期内 1.5） */
        java.math.BigDecimal transitionRentMultiplier,
        /** 成都：搬迁期月数（不超过 6） */
        Integer relocationMonths
) {
}
'''

FILES['biz/dto/TerminationVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.SettleStatus;
import com.yundao.bp.biz.constant.TerminationStatus;
import com.yundao.bp.biz.entity.BizTermination;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 退租单视图（含"能否办结"的派生判定）。
 */
public record TerminationVO(
        Long id,
        String terminationNo,
        Long contractId,
        Long houseId,
        Long personId,
        String terminationType,
        LocalDateTime applyTime,
        LocalDate planExitDate,
        LocalDate actualExitDate,
        String exitReason,
        String inspectStatus,
        String inspectResult,
        BigDecimal damageAmount,
        BigDecimal settleAmount,
        BigDecimal depositRefund,
        BigDecimal arrearsAmount,
        String settleStatus,
        String settleStatusLabel,
        String terminationStatus,
        String terminationStatusLabel,
        Boolean houseReleased,
        Boolean grantRevoked,
        LocalDate transitionStartDate,
        LocalDate transitionEndDate,
        Integer transitionMonths,
        BigDecimal transitionRentMultiplier,
        LocalDate relocationStartDate,
        LocalDate relocationEndDate,
        Boolean enforceFlag,
        String enforceCourt,
        String itemHandlerName,
        Boolean notaryFlag,
        String notaryNo,
        LocalDate banReapplyEndDate,
        /** 派生：四个前置是否齐备（验房通过 + 结算完成 + 房源已释放 + 授权已回收） */
        Boolean readyToComplete,
        /** 派生：是否逾期未退房（计划退房日已过仍无实际退房日） */
        Boolean overdueExit,
        LocalDateTime createTime
) {
    public static TerminationVO from(BizTermination e) {
        if (e == null) {
            return null;
        }
        TerminationStatus st;
        try {
            st = TerminationStatus.valueOf(e.getTerminationStatus());
        } catch (IllegalArgumentException ex) {
            st = TerminationStatus.APPLYING;
        }
        SettleStatus settle;
        try {
            settle = SettleStatus.valueOf(
                    e.getSettleStatus() == null ? "PENDING" : e.getSettleStatus());
        } catch (IllegalArgumentException ex) {
            settle = SettleStatus.PENDING;
        }
        boolean inspectOk = "PASSED".equals(e.getInspectStatus());
        boolean settleOk = settle == SettleStatus.SETTLED || settle == SettleStatus.WAIVED;
        boolean released = e.getHouseReleased() != null && e.getHouseReleased() == 1;
        boolean revoked = e.getGrantRevoked() != null && e.getGrantRevoked() == 1;
        boolean ready = inspectOk && settleOk && released && revoked;
        boolean overdue = e.getPlanExitDate() != null && e.getActualExitDate() == null
                && LocalDate.now().isAfter(e.getPlanExitDate())
                && !st.isTerminal();
        return new TerminationVO(e.getId(), e.getTerminationNo(), e.getContractId(),
                e.getHouseId(), e.getPersonId(), e.getTerminationType(), e.getApplyTime(),
                e.getPlanExitDate(), e.getActualExitDate(), e.getExitReason(),
                e.getInspectStatus(), e.getInspectResult(), e.getDamageAmount(),
                e.getSettleAmount(), e.getDepositRefund(), e.getArrearsAmount(),
                e.getSettleStatus(), settle.label(), e.getTerminationStatus(), st.label(),
                released, revoked, e.getTransitionStartDate(), e.getTransitionEndDate(),
                e.getTransitionMonths(), e.getTransitionRentMultiplier(),
                e.getRelocationStartDate(), e.getRelocationEndDate(),
                e.getEnforceFlag() != null && e.getEnforceFlag() == 1,
                e.getEnforceCourt(), e.getItemHandlerName(),
                e.getNotaryFlag() != null && e.getNotaryFlag() == 1, e.getNotaryNo(),
                e.getBanReapplyEndDate(), ready, overdue, e.getCreateTime());
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
