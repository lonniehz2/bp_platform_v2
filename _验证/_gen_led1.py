# -*- coding: utf-8 -*-
"""生成 fin 收尾：催缴/对账/流水（常量+实体+Mapper+DTO）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ==================== 常量 ====================
FILES['fin/constant/DunningType.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 催缴方式（对应 {@code bp_fin_dunning_record.dunning_type}）。
 */
public enum DunningType {

    SMS("短信"),
    WECHAT("微信"),
    PHONE("电话"),
    VISIT("上门"),
    NOTICE("通知书"),
    PLATFORM("平台消息");

    private final String label;

    DunningType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否需要留证（照片/通话记录）。 */
    public boolean needsEvidence() {
        return this == VISIT || this == PHONE;
    }
}
'''

FILES['fin/constant/ReconcileStatus.java'] = '''package com.yundao.bp.fin.constant;

import java.util.Set;

/**
 * 对账状态（对应 {@code bp_fin_reconcile.reconcile_status}）。
 *
 * <pre>
 *   MATCHED 一致（终态）
 *   DIFF 有差异 ──人工处理──> HANDLED 已处理（终态）
 * </pre>
 */
public enum ReconcileStatus {

    MATCHED("一致"),
    DIFF("有差异"),
    HANDLED("已处理");

    private final String label;

    ReconcileStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return this == MATCHED || this == HANDLED;
    }

    public static Set<ReconcileStatus> nextOf(ReconcileStatus from) {
        return switch (from) {
            case DIFF -> Set.of(HANDLED, MATCHED);
            case MATCHED, HANDLED -> Set.of();
        };
    }
}
'''

FILES['fin/constant/FlowType.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 资金流水类型（对应 {@code bp_fin_cash_flow.flow_type}）。
 *
 * <p>金额带符号：收入为正、支出为负，便于直接求和得到净额。
 */
public enum FlowType {

    INCOME("收入"),
    EXPENSE("支出"),
    TRANSFER("转账"),
    ADJUST("调整");

    private final String label;

    FlowType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 该类型金额应为正还是负。 */
    public boolean positive() {
        return this == INCOME;
    }
}
'''

FILES['fin/constant/FlowBizType.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 流水关联的业务单据类型（对应 {@code bp_fin_cash_flow.biz_type}）。
 */
public enum FlowBizType {

    BILL("账单"),
    PAYMENT("收款"),
    REFUND("退款"),
    SUBSIDY("补贴"),
    OTHER("其他");

    private final String label;

    FlowBizType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

FILES['fin/constant/VerifyStatus.java'] = '''package com.yundao.bp.fin.constant;

/**
 * 流水校验状态（对应 {@code bp_fin_cash_flow.verify_status}）。
 *
 * <p>业务数据变更后（如账单减免、退款冲销），流水金额可能与业务账面不一致，
 * 校验用于标记这类差异。
 */
public enum VerifyStatus {

    UNVERIFIED("未校验"),
    VERIFIED("已校验"),
    ABNORMAL("异常");

    private final String label;

    VerifyStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
'''

# ==================== 实体 ====================
FILES['fin/entity/FinDunningRecord.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 催缴记录。对应 {@code bp_fin_dunning_record}。
 *
 * <p>同一账单可多次催缴，{@code dunning_no} 为第几次催缴（1、2、3…）。
 */
@Data
@TableName("bp_fin_dunning_record")
public class FinDunningRecord {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long billId;
    private Long personId;

    /** 第几次催缴 */
    private Integer dunningNo;
    /** SMS / WECHAT / PHONE / VISIT / NOTICE / PLATFORM */
    private String dunningType;
    private LocalDateTime dunningTime;
    private String dunningContent;
    private String dunningResult;
    /** 佐证（上门照片/通话记录） */
    private String evidenceUrl;
    private Long operatorId;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
}
'''

FILES['fin/entity/FinReconcile.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 财务对账记录。对应 {@code bp_fin_reconcile}。
 */
@Data
@TableName("bp_fin_reconcile")
public class FinReconcile {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String reconcileNo;
    private Long accountSetId;

    private LocalDate reconcileDate;
    /** CHANNEL / DAILY / MANUAL */
    private String reconcileType;
    private String payChannel;

    /** 系统金额 */
    private BigDecimal systemAmount;
    /** 渠道金额 */
    private BigDecimal channelAmount;
    /** 差异金额 = 系统 - 渠道 */
    private BigDecimal diffAmount;
    private Integer diffCount;

    /** MATCHED / DIFF / HANDLED */
    private String reconcileStatus;
    private String diffDetailUrl;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

FILES['fin/entity/FinCashFlow.java'] = '''package com.yundao.bp.fin.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 资金流水。对应 {@code bp_fin_cash_flow}。
 *
 * <p>每一笔收付都留一条流水，金额<b>带符号</b>（收入为正、支出为负），
 * 便于直接求和计算净流入。
 */
@Data
@TableName("bp_fin_cash_flow")
public class FinCashFlow {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long accountSetId;
    private String flowNo;

    /** INCOME / EXPENSE / TRANSFER / ADJUST */
    private String flowType;
    /** BILL / PAYMENT / REFUND / SUBSIDY / OTHER */
    private String bizType;
    private Long bizId;

    /** 金额（正负） */
    private BigDecimal amount;
    private BigDecimal balanceAfter;
    private LocalDateTime flowTime;

    /** UNVERIFIED / VERIFIED / ABNORMAL */
    private String verifyStatus;
    private String verifyRemark;

    private LocalDateTime createTime;
}
'''

for mapper, entity in (('FinDunningRecordMapper', 'FinDunningRecord'),
                       ('FinReconcileMapper', 'FinReconcile'),
                       ('FinCashFlowMapper', 'FinCashFlow')):
    FILES['fin/mapper/%s.java' % mapper] = '''package com.yundao.bp.fin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.fin.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

# ==================== DTO ====================
FILES['fin/dto/DunningCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 登记一次催缴。
 */
public record DunningCreateCmd(

        @NotNull(message = "账单不能为空")
        Long billId,

        Long personId,

        @NotBlank(message = "催缴方式不能为空")
        @Pattern(regexp = "SMS|WECHAT|PHONE|VISIT|NOTICE|PLATFORM", message = "催缴方式不合法")
        String dunningType,

        @Size(max = 1000, message = "催缴内容不能超过 1000 字")
        String dunningContent,

        String dunningResult,

        /** 佐证 URL（上门照片/通话记录）；上门、电话建议必填 */
        String evidenceUrl,

        Long operatorId
) {
}
'''

FILES['fin/dto/ReconcileCreateCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 发起对账。
 *
 * <p>{@code systemAmount} 不传时由系统按当日该渠道收款单自动汇总；
 * {@code channelAmount} 为渠道/银行回单金额（人工录入或导入）。
 */
public record ReconcileCreateCmd(

        @NotNull(message = "对账日期不能为空")
        LocalDate reconcileDate,

        @NotBlank(message = "对账类型不能为空")
        @Pattern(regexp = "CHANNEL|DAILY|MANUAL", message = "对账类型不合法")
        String reconcileType,

        /** CHANNEL 类必填；不传则汇总全部渠道 */
        String payChannel,

        /** 系统金额；不传自动汇总 */
        BigDecimal systemAmount,

        @NotNull(message = "渠道金额不能为空")
        BigDecimal channelAmount,

        /** 差异笔数；不传默认 0 */
        Integer diffCount,

        String diffDetailUrl
) {
}
'''

FILES['fin/dto/CashFlowRecordCmd.java'] = '''package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 手工登记资金流水（正常业务流水由系统自动写入）。
 */
public record CashFlowRecordCmd(

        @NotNull(message = "流水类型不能为空")
        @Pattern(regexp = "INCOME|EXPENSE|TRANSFER|ADJUST", message = "流水类型不合法")
        String flowType,

        @Pattern(regexp = "^$|BILL|PAYMENT|REFUND|SUBSIDY|OTHER", message = "业务类型不合法")
        String bizType,

        Long bizId,

        @NotNull(message = "金额不能为空")
        BigDecimal amount,

        String remark
) {
}
'''

FILES['fin/dto/DunningVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.DunningType;
import com.yundao.bp.fin.entity.FinDunningRecord;
import java.time.LocalDateTime;

/**
 * 催缴记录视图。
 */
public record DunningVO(
        Long id,
        Long billId,
        Long personId,
        Integer dunningNo,
        String dunningType,
        String dunningTypeLabel,
        LocalDateTime dunningTime,
        String dunningContent,
        String dunningResult,
        String evidenceUrl,
        Long operatorId,
        LocalDateTime createTime
) {
    public static DunningVO from(FinDunningRecord e) {
        if (e == null) {
            return null;
        }
        DunningType t;
        try {
            t = DunningType.valueOf(e.getDunningType());
        } catch (IllegalArgumentException ex) {
            t = DunningType.SMS;
        }
        return new DunningVO(e.getId(), e.getBillId(), e.getPersonId(), e.getDunningNo(),
                e.getDunningType(), t.label(), e.getDunningTime(), e.getDunningContent(),
                e.getDunningResult(), e.getEvidenceUrl(), e.getOperatorId(), e.getCreateTime());
    }
}
'''

FILES['fin/dto/ReconcileVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.ReconcileStatus;
import com.yundao.bp.fin.entity.FinReconcile;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 对账记录视图。
 */
public record ReconcileVO(
        Long id,
        String reconcileNo,
        LocalDate reconcileDate,
        String reconcileType,
        String payChannel,
        BigDecimal systemAmount,
        BigDecimal channelAmount,
        BigDecimal diffAmount,
        Integer diffCount,
        String reconcileStatus,
        String reconcileStatusLabel,
        /** 派生：是否账实相符 */
        Boolean matched,
        String diffDetailUrl,
        LocalDateTime createTime
) {
    public static ReconcileVO from(FinReconcile e) {
        if (e == null) {
            return null;
        }
        ReconcileStatus st;
        try {
            st = ReconcileStatus.valueOf(e.getReconcileStatus());
        } catch (IllegalArgumentException ex) {
            st = ReconcileStatus.DIFF;
        }
        BigDecimal diff = e.getDiffAmount() == null ? BigDecimal.ZERO : e.getDiffAmount();
        return new ReconcileVO(e.getId(), e.getReconcileNo(), e.getReconcileDate(),
                e.getReconcileType(), e.getPayChannel(), e.getSystemAmount(),
                e.getChannelAmount(), e.getDiffAmount(), e.getDiffCount(),
                e.getReconcileStatus(), st.label(), diff.compareTo(BigDecimal.ZERO) == 0,
                e.getDiffDetailUrl(), e.getCreateTime());
    }
}
'''

FILES['fin/dto/CashFlowVO.java'] = '''package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.FlowType;
import com.yundao.bp.fin.constant.VerifyStatus;
import com.yundao.bp.fin.entity.FinCashFlow;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 资金流水视图。
 */
public record CashFlowVO(
        Long id,
        String flowNo,
        String flowType,
        String flowTypeLabel,
        String bizType,
        Long bizId,
        BigDecimal amount,
        BigDecimal balanceAfter,
        LocalDateTime flowTime,
        String verifyStatus,
        String verifyStatusLabel,
        String verifyRemark,
        LocalDateTime createTime
) {
    public static CashFlowVO from(FinCashFlow e) {
        if (e == null) {
            return null;
        }
        FlowType ft;
        try {
            ft = FlowType.valueOf(e.getFlowType());
        } catch (IllegalArgumentException ex) {
            ft = FlowType.INCOME;
        }
        VerifyStatus vs;
        try {
            vs = VerifyStatus.valueOf(e.getVerifyStatus());
        } catch (IllegalArgumentException ex) {
            vs = VerifyStatus.UNVERIFIED;
        }
        return new CashFlowVO(e.getId(), e.getFlowNo(), e.getFlowType(), ft.label(),
                e.getBizType(), e.getBizId(), e.getAmount(), e.getBalanceAfter(),
                e.getFlowTime(), e.getVerifyStatus(), vs.label(), e.getVerifyRemark(),
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
