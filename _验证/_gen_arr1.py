# -*- coding: utf-8 -*-
"""生成 fin 欠费停权处置"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/constant/ArrearsActionType.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 欠费处置动作（对应 {@code bp_fin_arrears_action.action_type}）。
 */
public enum ArrearsActionType {

    NOTIFY("通知催缴"),
    FREEZE("冻结权限"),
    UNFREEZE("解冻"),
    RESTRICT("限制续租"),
    EXPIRE("到期不续"),
    LEGAL("司法程序");

    private final String label;

    ArrearsActionType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要联动授权模块。 */
    public boolean touchesGrant() {
        return this == FREEZE || this == UNFREEZE;
    }
}
'''

FILES['fin/constant/FreezeScope.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 冻结范围（对应 {@code bp_fin_arrears_action.freeze_scope}）。
 *
 * <p>⭐⭐ <b>安全底线（决策 D19）</b>：欠费停权<b>不得停用大门门禁</b>。
 * 原因：
 * <ul>
 *   <li><b>消防与应急逃生</b>：大门是唯一疏散通道，停用会造成安全隐患甚至法律责任</li>
 *   <li><b>基本居住权</b>：房门锁停用已足以施压，停大门等于剥夺基本生活与进出权利</li>
 *   <li><b>合规要求</b>：多地保障房管理办法明确不得以欠费为由影响居住安全</li>
 * </ul>
 *
 * <p>因此系统默认且推荐 {@link #EXCLUDE_MAIN_DOOR}；
 * {@link #ALL} 需显式确认风险才能使用，且会被记录审计。
 */
public enum FreezeScope {

    /** 全部设备（含大门）—— 默认禁止，需显式确认风险 */
    ALL("全部设备（含大门）", true),
    /** 仅房门锁 —— 过度收窄，可能影响正常进出楼道 */
    ROOM_LOCK("仅房门锁", false),
    /** 排除大门门禁 —— ⭐ 推荐与默认，安全底线 */
    EXCLUDE_MAIN_DOOR("排除大门门禁（安全底线）", false);

    private final String label;
    private final boolean risky;

    FreezeScope(String label, boolean risky) {
        this.label = label;
        this.risky = risky;
    }

    public String label() {
        return label;
    }

    /** 是否属于有安全风险的范围（需人工确认）。 */
    public boolean risky() {
        return risky;
    }
}
'''

FILES['fin/constant/ArrearsActionStatus.java'] = '''package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 欠费处置单状态（对应 {@code bp_fin_arrears_action.action_status}）。
 *
 * <pre>
 *   PENDING 待执行 ──执行──> EXECUTED 已执行 ──缴清/撤销──> REVOKED 已撤销
 *        │                        │
 *        └──撤销──> REVOKED        └──执行失败──> FAILED（可重试回 PENDING）
 * </pre>
 */
public enum ArrearsActionStatus {

    PENDING("待执行"),
    EXECUTED("已执行"),
    REVOKED("已撤销"),
    FAILED("执行失败");

    private final String label;

    ArrearsActionStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == REVOKED;
    }

    public static Set<ArrearsActionStatus> nextOf(ArrearsActionStatus from) {
        return switch (from) {
            case PENDING -> Set.of(EXECUTED, REVOKED, FAILED);
            case EXECUTED -> Set.of(REVOKED);
            case FAILED -> Set.of(PENDING, REVOKED);
            case REVOKED -> Set.of();
        };
    }
}
'''

FILES['fin/entity/FinArrearsAction.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 欠费停权处置记录。对应 {@code bp_fin_arrears_action}。
 */
@Data
@TableName("bp_fin_arrears_action")
public class FinArrearsAction {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String actionNo;

    private Long contractId;
    private Long personId;

    private BigDecimal arrearsAmount;
    private Integer overdueDays;

    /** AUTO / MANUAL */
    private String triggerType;
    /** NOTIFY / FREEZE / UNFREEZE / RESTRICT / EXPIRE / LEGAL */
    private String actionType;
    /** ALL / ROOM_LOCK / EXCLUDE_MAIN_DOOR */
    private String freezeScope;

    /** PENDING / EXECUTED / REVOKED / FAILED */
    private String actionStatus;
    private LocalDateTime executeTime;
    private Long grantTaskId;
    private String revokeReason;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['fin/mapper/FinArrearsActionMapper.java'] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.FinArrearsAction;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface FinArrearsActionMapper extends BaseMapper<FinArrearsAction> {
}
'''

FILES['fin/dto/ArrearsActionCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 创建欠费处置单。
 *
 * @param freezeScope         冻结范围；<b>默认 EXCLUDE_MAIN_DOOR（安全底线，不停大门）</b>。
 *                            {@code ALL} 会停用大门，需 {@code confirmSafetyRisk=true} 才允许。
 * @param confirmSafetyRisk   是否已确认"停用大门"的安全风险（默认 false）
 */
public record ArrearsActionCreateCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "欠费金额不能为空")
        @DecimalMin(value = "0.01", message = "欠费金额必须大于 0")
        BigDecimal arrearsAmount,

        Integer overdueDays,

        @NotBlank(message = "处置动作不能为空")
        @Pattern(regexp = "NOTIFY|FREEZE|UNFREEZE|RESTRICT|EXPIRE|LEGAL",
                message = "处置动作不合法")
        String actionType,

        @Pattern(regexp = "^$|ALL|ROOM_LOCK|EXCLUDE_MAIN_DOOR", message = "冻结范围不合法")
        String freezeScope,

        /** 是否已确认停用大门的安全风险 */
        Boolean confirmSafetyRisk,

        @Pattern(regexp = "^$|AUTO|MANUAL", message = "触发方式不合法")
        String triggerType
) {
}
'''

FILES['fin/dto/ArrearsActionVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.ArrearsActionStatus;
import com.yundao.bp.fin.constant.FreezeScope;
import com.yundao.bp.fin.entity.FinArrearsAction;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 欠费处置单视图。
 */
public record ArrearsActionVO(
        Long id,
        String actionNo,
        Long contractId,
        Long personId,
        BigDecimal arrearsAmount,
        Integer overdueDays,
        String triggerType,
        String actionType,
        String freezeScope,
        String freezeScopeLabel,
        /** 是否停用了大门（安全底线被突破，应为 false） */
        Boolean freezesMainDoor,
        String actionStatus,
        String actionStatusLabel,
        LocalDateTime executeTime,
        Long grantTaskId,
        String revokeReason,
        LocalDateTime createTime
) {
    public static ArrearsActionVO from(FinArrearsAction e) {
        if (e == null) {
            return null;
        }
        ArrearsActionStatus st;
        try {
            st = ArrearsActionStatus.valueOf(e.getActionStatus());
        } catch (IllegalArgumentException ex) {
            st = ArrearsActionStatus.PENDING;
        }
        FreezeScope scope;
        try {
            scope = e.getFreezeScope() == null ? FreezeScope.EXCLUDE_MAIN_DOOR
                    : FreezeScope.valueOf(e.getFreezeScope());
        } catch (IllegalArgumentException ex) {
            scope = FreezeScope.EXCLUDE_MAIN_DOOR;
        }
        return new ArrearsActionVO(e.getId(), e.getActionNo(), e.getContractId(),
                e.getPersonId(), e.getArrearsAmount(), e.getOverdueDays(),
                e.getTriggerType(), e.getActionType(), e.getFreezeScope(), scope.label(),
                scope == FreezeScope.ALL, e.getActionStatus(), st.label(),
                e.getExecuteTime(), e.getGrantTaskId(), e.getRevokeReason(), e.getCreateTime());
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
