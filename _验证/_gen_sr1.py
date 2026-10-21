# -*- coding: utf-8 -*-
"""生成短租订单（第一部分）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/constant/ShortRentOrderStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 短租订单状态（对应 {@code bp_biz_short_rent_order.order_status}）。
 *
 * <pre>
 *   PENDING 待确认 ──确认──> CONFIRMED 已确认 ──入住──> CHECKED_IN 已入住 ──退房──> CHECKED_OUT 已退房（终态）
 *        │                        │                          │
 *        └────取消───> CANCELLED 已取消（终态）                 │
 *                                 └──未到──> NO_SHOW 未到（终态）
 * </pre>
 *
 * <p>取消/退房会释放对应的日房态，让房源可再次售卖。
 */
public enum ShortRentOrderStatus {

    PENDING("待确认", false),
    CONFIRMED("已确认", false),
    CHECKED_IN("已入住", false),
    CHECKED_OUT("已退房", true),
    CANCELLED("已取消", true),
    NO_SHOW("未到", true);

    private final String label;
    private final boolean terminal;

    ShortRentOrderStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍占用房态（需在取消/退房时释放）。 */
    public boolean occupiesCalendar() {
        return this != CANCELLED && this != NO_SHOW;
    }

    public static Set<ShortRentOrderStatus> nextOf(ShortRentOrderStatus from) {
        return switch (from) {
            case PENDING -> Set.of(CONFIRMED, CANCELLED);
            case CONFIRMED -> Set.of(CHECKED_IN, CANCELLED, NO_SHOW);
            case CHECKED_IN -> Set.of(CHECKED_OUT);
            case CHECKED_OUT, CANCELLED, NO_SHOW -> Set.of();
        };
    }
}
'''

FILES['biz/entity/BizShortRentOrder.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 短租订单。对应 {@code bp_biz_short_rent_order}。
 *
 * <p>与长租合同的区别：<b>时刻级</b>入住/退房 + <b>房晚</b>计价 + 实名登记。
 */
@Data
@TableName("bp_biz_short_rent_order")
public class BizShortRentOrder {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String orderNo;
    private Long orgId;
    private Long houseId;
    private Long spaceId;

    /** DIRECT / OTA / WECHAT / PHONE / WALKIN / OTHER */
    private String sourceChannel;

    private String guestName;
    private String guestPhone;
    /** 证件号（加密存储） */
    private String guestIdCard;
    private Integer guestCount;

    /** 入住时刻（精确到时分） */
    private LocalDateTime checkInTime;
    /** 退房时刻（精确到时分） */
    private LocalDateTime checkOutTime;
    /** 房晚数 */
    private Integer nightCount;

    private BigDecimal roomAmount;
    private BigDecimal extraAmount;
    private BigDecimal discountAmount;
    private BigDecimal totalAmount;
    private BigDecimal paidAmount;

    /** PENDING / CONFIRMED / CHECKED_IN / CHECKED_OUT / CANCELLED / NO_SHOW */
    private String orderStatus;
    /** UNPAID / PAID / REFUNDED */
    private String payStatus;

    private String cancelReason;
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

FILES['biz/mapper/BizShortRentOrderMapper.java'] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.BizShortRentOrder;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface BizShortRentOrderMapper extends BaseMapper<BizShortRentOrder> {
}
'''

FILES['biz/dto/ShortRentOrderCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 创建短租订单。
 *
 * <p><b>时刻级</b>：入住/退房精确到时分，适配酒店 14:00 入住、次日 12:00 退房。
 *
 * <p><b>房晚口径</b>：按日期差计算（左闭右开）——
 * 11-01 14:00 → 11-02 12:00 为 <b>1 晚</b>；
 * 同日入住退房视为钟点房，按 <b>1 晚</b> 计。
 */
public record ShortRentOrderCreateCmd(

        @NotNull(message = "房源不能为空")
        Long houseId,

        Long spaceId,

        @NotBlank(message = "来源渠道不能为空")
        @Pattern(regexp = "DIRECT|OTA|WECHAT|PHONE|WALKIN|OTHER", message = "来源渠道不合法")
        String sourceChannel,

        /** 网约房必须实名 */
        @NotBlank(message = "住客姓名不能为空（网约房需实名登记）")
        String guestName,

        String guestPhone,
        String guestIdCard,

        @Min(value = 1, message = "入住人数至少 1 人")
        Integer guestCount,

        @NotNull(message = "入住时刻不能为空")
        LocalDateTime checkInTime,

        @NotNull(message = "退房时刻不能为空")
        LocalDateTime checkOutTime,

        /** 房晚单价；不传则按房源默认价（本模块不自动取价，由前端/渠道传入） */
        @NotNull(message = "房晚单价不能为空")
        BigDecimal nightlyPrice,

        BigDecimal extraAmount,
        BigDecimal discountAmount,
        BigDecimal paidAmount,
        String remark
) {
}
'''

FILES['biz/dto/ShortRentOrderVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ShortRentOrderStatus;
import com.yundao.bp.biz.entity.BizShortRentOrder;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 短租订单视图。
 */
public record ShortRentOrderVO(
        Long id,
        String orderNo,
        Long orgId,
        Long houseId,
        Long spaceId,
        String sourceChannel,
        String guestName,
        String guestPhone,
        Integer guestCount,
        LocalDateTime checkInTime,
        LocalDateTime checkOutTime,
        Integer nightCount,
        BigDecimal roomAmount,
        BigDecimal extraAmount,
        BigDecimal discountAmount,
        BigDecimal totalAmount,
        BigDecimal paidAmount,
        String orderStatus,
        String orderStatusLabel,
        String payStatus,
        String cancelReason,
        String remark,
        /** 派生：订单占用的日期区间（日历口径，左闭右开） */
        LocalDate occupyFrom,
        LocalDate occupyTo,
        /** 派生：待收金额 = 总额 - 已付 */
        BigDecimal unpaidAmount,
        /** 派生：是否已过退房时刻但仍是"已入住"（超时未退房） */
        Boolean overdueCheckout,
        LocalDateTime createTime
) {
    public static ShortRentOrderVO from(BizShortRentOrder e) {
        if (e == null) {
            return null;
        }
        ShortRentOrderStatus st;
        try {
            st = ShortRentOrderStatus.valueOf(e.getOrderStatus());
        } catch (IllegalArgumentException ex) {
            st = ShortRentOrderStatus.PENDING;
        }
        LocalDate from = e.getCheckInTime() == null ? null : e.getCheckInTime().toLocalDate();
        LocalDate to = e.getCheckOutTime() == null ? null : e.getCheckOutTime().toLocalDate();
        BigDecimal total = e.getTotalAmount() == null ? BigDecimal.ZERO : e.getTotalAmount();
        BigDecimal paid = e.getPaidAmount() == null ? BigDecimal.ZERO : e.getPaidAmount();
        boolean overdue = st == ShortRentOrderStatus.CHECKED_IN
                && e.getCheckOutTime() != null
                && LocalDateTime.now().isAfter(e.getCheckOutTime());
        return new ShortRentOrderVO(e.getId(), e.getOrderNo(), e.getOrgId(), e.getHouseId(),
                e.getSpaceId(), e.getSourceChannel(), e.getGuestName(), e.getGuestPhone(),
                e.getGuestCount(), e.getCheckInTime(), e.getCheckOutTime(), e.getNightCount(),
                e.getRoomAmount(), e.getExtraAmount(), e.getDiscountAmount(), e.getTotalAmount(),
                e.getPaidAmount(), e.getOrderStatus(), st.label(), e.getPayStatus(),
                e.getCancelReason(), e.getRemark(), from, to, total.subtract(paid), overdue,
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
