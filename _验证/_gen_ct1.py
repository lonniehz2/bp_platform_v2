# -*- coding: utf-8 -*-
"""生成 biz 合同模块"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/constant/ContractStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 合同状态机（对应 {@code bp_biz_contract.contract_status}）。
 *
 * <pre>
 *   DRAFT 草稿 ──提交签约──> PENDING_SIGN 待签约 ──发起──> SIGNING 签约中
 *                                                          │
 *                                                    签署完成
 *                                                          ↓
 *   RENEWING 续签中 ←──续签── EFFECTIVE 履约中 ──到期──> EXPIRED 已到期
 *                                  │
 *                             ──退租/终止──> TERMINATED 已终止
 *   DRAFT/PENDING_SIGN ──作废──> CANCELLED
 * </pre>
 *
 * <p><b>业务要害</b>：{@code EFFECTIVE} 时会按 {@code auto_grant} 自动下发权限，
 * {@code TERMINATED/EXPIRED} 时按 {@code auto_expire} 自动撤权 —— 这是
 * "合同驱动授权"的关键联动点。
 */
public enum ContractStatus {

    DRAFT("草稿", false),
    PENDING_SIGN("待签约", false),
    SIGNING("签约中", false),
    EFFECTIVE("履约中", false),
    RENEWING("续签中", false),
    EXPIRED("已到期", true),
    TERMINATED("已终止", true),
    CANCELLED("已作废", true);

    private final String label;
    private final boolean terminal;

    ContractStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否是"占房"状态（房源应显示已租）。 */
    public boolean isOccupying() {
        return this == EFFECTIVE || this == RENEWING;
    }

    public static Set<ContractStatus> nextOf(ContractStatus from) {
        return switch (from) {
            case DRAFT -> Set.of(PENDING_SIGN, CANCELLED);
            case PENDING_SIGN -> Set.of(SIGNING, CANCELLED);
            case SIGNING -> Set.of(EFFECTIVE, CANCELLED);
            case EFFECTIVE -> Set.of(RENEWING, EXPIRED, TERMINATED);
            case RENEWING -> Set.of(EFFECTIVE, TERMINATED);
            case EXPIRED, TERMINATED, CANCELLED -> Set.of();
        };
    }
}
'''

FILES['biz/entity/BizContract.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 合同（全生命周期）。对应 {@code bp_biz_contract}。
 */
@Data
@TableName("bp_biz_contract")
public class BizContract {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String contractNo;

    /** PUBLIC_RENTAL / AFFORDABLE / TALENT / LEASE / SERVICE / DORMITORY */
    private String contractType;
    private Long templateId;
    private Long allocationId;

    private Long orgId;
    private Long accountSetId;

    private Long lesseePersonId;
    private String lesseeName;
    private String lesseePhone;
    private String lesseeIdCardMask;
    private Long lessorOrgId;

    private Long houseId;
    private Long spaceId;
    private String houseAddress;
    private BigDecimal houseArea;

    private LocalDate leaseStart;
    private LocalDate leaseEnd;
    private Integer leaseMonths;

    private BigDecimal rentPrice;
    private String rentUnit;
    private BigDecimal monthlyRent;
    private BigDecimal depositAmount;
    private BigDecimal subsidyAmount;
    /** 实付月租金 = 月租金 - 月补贴 */
    private BigDecimal actualPay;

    /** MONTH / QUARTER / HALF_YEAR / YEAR */
    private String payCycle;
    private Integer payDay;
    private BigDecimal lateFeeRate;

    /** ELECTRONIC / PAPER / FACE */
    private String signType;
    private String signVendor;
    private LocalDateTime signTime;
    private String signFileUrl;
    private String signFlowId;

    /** DRAFT / PENDING_SIGN / SIGNING / EFFECTIVE / RENEWING / EXPIRED / TERMINATED / CANCELLED */
    private String contractStatus;
    private LocalDateTime effectiveTime;
    private LocalDateTime terminateTime;
    private String terminateReason;
    private Long parentContractId;

    private Integer autoGrant;
    private Integer autoExpire;
    private Integer arrearsStop;

    private String remark;

    @TableLogic
    private Integer isDeleted;

    @TableField(fill = FieldFill.INSERT)
    private String createBy;
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
'''

FILES['biz/mapper/BizContractMapper.java'] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.BizContract;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizContractMapper extends BaseMapper<BizContract> {
}
'''

FILES['biz/dto/ContractCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 起草合同。
 *
 * <p>金额口径：{@code actualPay = monthlyRent - subsidyAmount}（服务端计算，不接受前端传入）。
 */
public record ContractCreateCmd(

        @NotBlank(message = "合同类型不能为空")
        @Pattern(regexp = "PUBLIC_RENTAL|AFFORDABLE|TALENT|LEASE|SERVICE|DORMITORY",
                message = "合同类型不合法")
        String contractType,

        @NotNull(message = "签约组织不能为空")
        Long orgId,

        @NotNull(message = "出租方不能为空")
        Long lessorOrgId,

        @NotNull(message = "承租人不能为空")
        Long lesseePersonId,
        String lesseeName,
        String lesseePhone,
        String lesseeIdCardMask,

        @NotNull(message = "房源不能为空")
        Long houseId,
        @NotNull(message = "空间不能为空")
        Long spaceId,
        String houseAddress,
        BigDecimal houseArea,

        @NotNull(message = "起租日不能为空")
        LocalDate leaseStart,
        @NotNull(message = "止租日不能为空")
        LocalDate leaseEnd,

        @NotNull(message = "租金单价不能为空")
        @DecimalMin(value = "0", message = "租金单价不能为负")
        BigDecimal rentPrice,

        @Pattern(regexp = "^$|AREA_MONTH|HOUSE_MONTH|BED_MONTH|HOUSE_NIGHT",
                message = "租金单位不合法")
        String rentUnit,

        @NotNull(message = "月租金不能为空")
        @DecimalMin(value = "0", message = "月租金不能为负")
        BigDecimal monthlyRent,

        @DecimalMin(value = "0", message = "押金不能为负")
        BigDecimal depositAmount,

        @DecimalMin(value = "0", message = "补贴不能为负")
        BigDecimal subsidyAmount,

        @Pattern(regexp = "^$|MONTH|QUARTER|HALF_YEAR|YEAR", message = "缴费周期不合法")
        String payCycle,

        @Min(value = 1, message = "缴费日必须在 1-31")
        Integer payDay,

        @Pattern(regexp = "^$|ELECTRONIC|PAPER|FACE", message = "签署方式不合法")
        String signType,

        Long templateId,
        Long allocationId,
        Long parentContractId,

        BigDecimal lateFeeRate,
        String remark
) {
}
'''

FILES['biz/dto/ContractVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.entity.BizContract;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 合同视图（含派生指标）。
 */
public record ContractVO(
        Long id,
        String contractNo,
        String contractType,
        Long orgId,
        Long lessorOrgId,
        Long lesseePersonId,
        String lesseeName,
        String lesseePhone,
        String lesseeIdCardMask,
        Long houseId,
        Long spaceId,
        String houseAddress,
        BigDecimal houseArea,
        LocalDate leaseStart,
        LocalDate leaseEnd,
        Integer leaseMonths,
        BigDecimal rentPrice,
        String rentUnit,
        BigDecimal monthlyRent,
        BigDecimal depositAmount,
        BigDecimal subsidyAmount,
        BigDecimal actualPay,
        String payCycle,
        Integer payDay,
        String signType,
        LocalDateTime signTime,
        String contractStatus,
        String contractStatusLabel,
        LocalDateTime effectiveTime,
        LocalDateTime terminateTime,
        String terminateReason,
        Integer autoGrant,
        Integer autoExpire,
        Integer arrearsStop,
        /** 派生：距到期剩余天数（履约中才有意义，其它为 null） */
        Long daysToExpire,
        /** 派生：是否即将到期（30 天内） */
        Boolean expiringSoon,
        /** 派生：是否占房（履约中/续签中） */
        Boolean occupying,
        String remark,
        LocalDateTime createTime
) {
    public static ContractVO from(BizContract e) {
        if (e == null) {
            return null;
        }
        ContractStatus st;
        try {
            st = ContractStatus.valueOf(e.getContractStatus());
        } catch (IllegalArgumentException ex) {
            st = ContractStatus.DRAFT;
        }
        Long daysToExpire = null;
        boolean expiringSoon = false;
        if (st.isOccupying() && e.getLeaseEnd() != null) {
            daysToExpire = ChronoUnit.DAYS.between(LocalDate.now(), e.getLeaseEnd());
            expiringSoon = daysToExpire >= 0 && daysToExpire <= 30;
        }
        return new ContractVO(e.getId(), e.getContractNo(), e.getContractType(), e.getOrgId(),
                e.getLessorOrgId(), e.getLesseePersonId(), e.getLesseeName(), e.getLesseePhone(),
                e.getLesseeIdCardMask(), e.getHouseId(), e.getSpaceId(), e.getHouseAddress(),
                e.getHouseArea(), e.getLeaseStart(), e.getLeaseEnd(), e.getLeaseMonths(),
                e.getRentPrice(), e.getRentUnit(), e.getMonthlyRent(), e.getDepositAmount(),
                e.getSubsidyAmount(), e.getActualPay(), e.getPayCycle(), e.getPayDay(),
                e.getSignType(), e.getSignTime(), e.getContractStatus(), st.label(),
                e.getEffectiveTime(), e.getTerminateTime(), e.getTerminateReason(),
                e.getAutoGrant(), e.getAutoExpire(), e.getArrearsStop(),
                daysToExpire, expiringSoon, st.isOccupying(), e.getRemark(), e.getCreateTime());
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
