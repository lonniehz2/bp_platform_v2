# -*- coding: utf-8 -*-
"""生成配租模块（常量 + 实体 + Mapper + DTO）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ==================== 常量 ====================
FILES['biz/constant/QueueStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 轮候状态（对应 {@code bp_biz_waiting_queue.queue_status}）。
 *
 * <pre>
 *   WAITING 轮候中 ──中签──> WON 已中签 ──配租成功──> ALLOCATED 已配租（终态）
 *        │                    │
 *        ├──冻结──> FROZEN ────┘（解冻回 WAITING）
 *        ├──退出──> EXITED（终态）
 *        └──资格过期──> EXPIRED（终态）
 * </pre>
 */
public enum QueueStatus {

    WAITING("轮候中", false),
    WON("已中签", false),
    ALLOCATED("已配租", true),
    FROZEN("已冻结", false),
    EXITED("已退出", true),
    EXPIRED("已过期", true);

    private final String label;
    private final boolean terminal;

    QueueStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否还能被摇号/配租选中。 */
    public boolean selectable() {
        return this == WAITING;
    }

    public static Set<QueueStatus> nextOf(QueueStatus from) {
        return switch (from) {
            case WAITING -> Set.of(WON, FROZEN, EXITED, EXPIRED);
            case FROZEN -> Set.of(WAITING, EXITED);
            case WON -> Set.of(ALLOCATED, WAITING, EXITED);
            case ALLOCATED, EXITED, EXPIRED -> Set.of();
        };
    }
}
'''

FILES['biz/constant/BatchStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 配租批次状态（对应 {@code bp_biz_batch.batch_status}）。
 *
 * <pre>
 *   DRAFT 草稿 → PUBLISHED 已发布 → SIGNUP 报名中 → LOTTERY 摇号中
 *     → LOTTERY_DONE 摇号完成 → SELECTING 选房中 → ALLOCATED 已配租 → CLOSED 已结束
 *   任意阶段可 CANCELLED（终态）
 * </pre>
 */
public enum BatchStatus {

    DRAFT("草稿", false),
    PUBLISHED("已发布", false),
    SIGNUP("报名中", false),
    LOTTERY("摇号中", false),
    LOTTERY_DONE("摇号完成", false),
    SELECTING("选房中", false),
    ALLOCATED("已配租", false),
    CLOSED("已结束", true),
    CANCELLED("已取消", true);

    private final String label;
    private final boolean terminal;

    BatchStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否已过草稿阶段（可执行摇号）。 */
    public boolean canLottery() {
        return this == SIGNUP || this == PUBLISHED || this == LOTTERY;
    }

    public static Set<BatchStatus> nextOf(BatchStatus from) {
        return switch (from) {
            case DRAFT -> Set.of(PUBLISHED, CANCELLED);
            case PUBLISHED -> Set.of(SIGNUP, LOTTERY, CANCELLED);
            case SIGNUP -> Set.of(LOTTERY, CANCELLED);
            case LOTTERY -> Set.of(LOTTERY_DONE, CANCELLED);
            case LOTTERY_DONE -> Set.of(SELECTING, ALLOCATED, CANCELLED);
            case SELECTING -> Set.of(ALLOCATED, CANCELLED);
            case ALLOCATED -> Set.of(CLOSED, CANCELLED);
            case CLOSED, CANCELLED -> Set.of();
        };
    }
}
'''

FILES['biz/constant/AllocationStatus.java'] = '''package com.yundao.bp.biz.constant;

import java.util.Set;

/**
 * 配租单状态（对应 {@code bp_biz_allocation.allocation_status}）。
 *
 * <pre>
 *   PENDING_SIGN 待签约 ──签约──> SIGNED 已签约（终态）
 *        │
 *        ├──放弃/超时──> CANCELLED 已取消（终态）
 *        └──锁定超时──> EXPIRED 已过期（终态，房源自动释放）
 * </pre>
 */
public enum AllocationStatus {

    PENDING_SIGN("待签约", false),
    SIGNED("已签约", true),
    CANCELLED("已取消", true),
    EXPIRED("已过期", true);

    private final String label;
    private final boolean terminal;

    AllocationStatus(String label, boolean terminal) {
        this.label = label;
        this.terminal = terminal;
    }

    public String label() {
        return label;
    }

    public boolean isTerminal() {
        return terminal;
    }

    /** 是否仍占用（锁定）房源。 */
    public boolean holdsHouse() {
        return this == PENDING_SIGN;
    }

    public static Set<AllocationStatus> nextOf(AllocationStatus from) {
        return switch (from) {
            case PENDING_SIGN -> Set.of(SIGNED, CANCELLED, EXPIRED);
            case SIGNED, CANCELLED, EXPIRED -> Set.of();
        };
    }
}
'''

FILES['biz/constant/LotteryResultType.java'] = '''package com.yundao.bp.biz.constant;

/**
 * 摇号/选房结果类型（对应 {@code bp_biz_lottery_result.result_type}）。
 */
public enum LotteryResultType {

    WON("中签"),
    LOST("未中签"),
    WAITLIST("递补"),
    GIVE_UP("放弃");

    private final String label;

    LotteryResultType(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    /** 是否具备配租资格。 */
    public boolean canAllocate() {
        return this == WON || this == WAITLIST;
    }
}
'''

# ==================== 实体 ====================
FILES['biz/entity/BizWaitingQueue.java'] = '''package com.yundao.bp.biz.entity;

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
 * 轮候库记录。对应 {@code bp_biz_waiting_queue}。
 */
@Data
@TableName("bp_biz_waiting_queue")
public class BizWaitingQueue {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long personId;
    private Long applicationId;
    private String securityType;
    private Long orgId;

    private String waitingNo;
    /** 轮候排名（按总分动态计算） */
    private Integer waitingRank;
    /** 总得分 = 优先分 + 轮候时长分 */
    private BigDecimal totalScore;
    private BigDecimal priorityScore;
    private Integer waitDays;

    private LocalDateTime enterTime;
    private LocalDate validUntil;

    /** WAITING / WON / ALLOCATED / FROZEN / EXITED / EXPIRED */
    private String queueStatus;
    private String freezeReason;

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

FILES['biz/entity/BizBatch.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 配租批次。对应 {@code bp_biz_batch}。
 */
@Data
@TableName("bp_biz_batch")
public class BizBatch {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String batchNo;
    private String batchName;
    private Long orgId;
    private String securityType;

    /** LOTTERY / SELECT / DIRECT / SUPPLEMENT */
    private String batchType;

    private Integer houseCount;
    private Integer applicantCount;

    private LocalDateTime signupStart;
    private LocalDateTime signupEnd;
    private LocalDateTime lotteryTime;
    private LocalDateTime selectStart;
    private LocalDateTime selectEnd;

    /** 摇号随机种子（公证留痕，可复现） */
    private String lotterySeed;
    private String lotteryAlgo;
    private String notaryInfo;

    /** DRAFT / PUBLISHED / SIGNUP / LOTTERY / LOTTERY_DONE / SELECTING / ALLOCATED / CLOSED / CANCELLED */
    private String batchStatus;
    private String ruleConfig;
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

FILES['biz/entity/BizBatchHouse.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 批次可配房源池。对应 {@code bp_biz_batch_house}。
 */
@Data
@TableName("bp_biz_batch_house")
public class BizBatchHouse {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long batchId;
    private Long houseId;
    private Long spaceId;
    /** AVAILABLE / LOCKED / SELECTED / REMOVED */
    private String inPoolStatus;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

FILES['biz/entity/BizLotteryResult.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 摇号/选房结果。对应 {@code bp_biz_lottery_result}。
 */
@Data
@TableName("bp_biz_lottery_result")
public class BizLotteryResult {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long batchId;
    private Long personId;
    private Long applicationId;
    private Long waitingId;

    /** WON / LOST / WAITLIST / GIVE_UP */
    private String resultType;
    /** 摇号序号（随机生成，公证留痕） */
    private String lotterySeq;
    private Integer selectSeq;

    private Long houseId;
    private Long spaceId;
    private LocalDateTime selectTime;
    private String giveUpReason;

    /** PENDING / CONFIRMED / EXPIRED / GIVE_UP */
    private String resultStatus;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
'''

FILES['biz/entity/BizAllocation.java'] = '''package com.yundao.bp.biz.entity;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 配租单。对应 {@code bp_biz_allocation}。
 */
@Data
@TableName("bp_biz_allocation")
public class BizAllocation {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private String allocationNo;
    private Long batchId;
    private Long personId;
    private Long houseId;
    private Long spaceId;

    /** LOTTERY / SELECT / DIRECT / EXCHANGE */
    private String allocationType;
    private LocalDate allocationDate;
    private LocalDate planRentStart;
    private LocalDate planRentEnd;

    /** PENDING_SIGN / SIGNED / CANCELLED / EXPIRED */
    private String allocationStatus;
    /** 房源锁定到期时间（超时自动释放） */
    private LocalDateTime lockExpireTime;
    private String giveUpReason;

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

for mapper, entity in (('BizWaitingQueueMapper', 'BizWaitingQueue'),
                       ('BizBatchMapper', 'BizBatch'),
                       ('BizBatchHouseMapper', 'BizBatchHouse'),
                       ('BizLotteryResultMapper', 'BizLotteryResult'),
                       ('BizAllocationMapper', 'BizAllocation')):
    FILES['biz/mapper/%s.java' % mapper] = '''package com.yundao.bp.biz.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.biz.entity.%s;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %s extends BaseMapper<%s> {
}
''' % (entity, mapper, entity)

# ==================== DTO ====================
FILES['biz/dto/WaitingEnterCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 申请通过后加入轮候库。
 */
public record WaitingEnterCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "申请单不能为空")
        Long applicationId,

        @NotBlank(message = "保障类型不能为空")
        @Pattern(regexp = "PUBLIC|AFFORDABLE|TALENT|LOW_RENT", message = "保障类型不合法")
        String securityType,

        Long orgId,

        /** 优先条件分（如低保、残疾、优抚等，由业务按政策核定） */
        @DecimalMin(value = "0", message = "优先分不能为负")
        BigDecimal priorityScore,

        /** 轮候资格有效期；为空则不设限 */
        LocalDate validUntil
) {
}
'''

FILES['biz/dto/BatchCreateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 创建配租批次。
 *
 * @param houseIds 批次可配房源（创建时一并入池）
 */
public record BatchCreateCmd(

        @NotBlank(message = "批次名称不能为空")
        String batchName,

        @NotNull(message = "项目组织不能为空")
        Long orgId,

        @NotBlank(message = "保障类型不能为空")
        @Pattern(regexp = "PUBLIC|AFFORDABLE|TALENT|LOW_RENT", message = "保障类型不合法")
        String securityType,

        @NotBlank(message = "批次类型不能为空")
        @Pattern(regexp = "LOTTERY|SELECT|DIRECT|SUPPLEMENT", message = "批次类型不合法")
        String batchType,

        /** 可配房源 ID 列表 */
        List<Long> houseIds,

        LocalDateTime signupStart,
        LocalDateTime signupEnd,
        LocalDateTime lotteryTime,
        LocalDateTime selectStart,
        LocalDateTime selectEnd,

        String notaryInfo,
        String remark
) {
}
'''

FILES['biz/dto/LotteryRunCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotNull;

/**
 * 执行摇号。
 *
 * @param seed 随机种子；为空则由系统生成并落库（公证留痕、结果可复现）
 */
public record LotteryRunCmd(

        @NotNull(message = "批次不能为空")
        Long batchId,

        String seed,

        /** 公证信息（公证处/公证员/公证书号） */
        String notaryInfo
) {
}
'''

FILES['biz/dto/AllocateCmd.java'] = '''package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

/**
 * 生成配租单（用房源锁定给中签人）。
 *
 * @param lockHours 房源锁定小时数；超时未签约自动释放，默认 72 小时
 */
public record AllocateCmd(

        @NotNull(message = "批次不能为空")
        Long batchId,

        @NotNull(message = "房源不能为空")
        Long houseId,

        @NotNull(message = "承租人不能为空")
        Long personId,

        /** 摇号结果 ID（可空；为空则按批次+人员反查） */
        Long lotteryResultId,

        LocalDate planRentStart,
        LocalDate planRentEnd,

        Integer lockHours
) {
}
'''

FILES['biz/dto/WaitingVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.QueueStatus;
import com.yundao.bp.biz.entity.BizWaitingQueue;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 轮候记录视图。
 */
public record WaitingVO(
        Long id,
        String waitingNo,
        Long personId,
        Long applicationId,
        String securityType,
        Long orgId,
        Integer waitingRank,
        BigDecimal totalScore,
        BigDecimal priorityScore,
        /** 派生：实时轮候天数（按当前时间重算） */
        Integer liveWaitDays,
        LocalDateTime enterTime,
        LocalDate validUntil,
        String queueStatus,
        String queueStatusLabel,
        String freezeReason,
        Boolean expired
) {
    public static WaitingVO from(BizWaitingQueue e) {
        if (e == null) {
            return null;
        }
        QueueStatus st;
        try {
            st = QueueStatus.valueOf(e.getQueueStatus());
        } catch (IllegalArgumentException ex) {
            st = QueueStatus.WAITING;
        }
        int live = e.getEnterTime() == null ? 0
                : (int) ChronoUnit.DAYS.between(e.getEnterTime().toLocalDate(), LocalDate.now());
        boolean exp = e.getValidUntil() != null && e.getValidUntil().isBefore(LocalDate.now());
        return new WaitingVO(e.getId(), e.getWaitingNo(), e.getPersonId(), e.getApplicationId(),
                e.getSecurityType(), e.getOrgId(), e.getWaitingRank(), e.getTotalScore(),
                e.getPriorityScore(), live, e.getEnterTime(), e.getValidUntil(),
                e.getQueueStatus(), st.label(), e.getFreezeReason(), exp);
    }
}
'''

FILES['biz/dto/BatchVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.BatchStatus;
import com.yundao.bp.biz.entity.BizBatch;
import java.time.LocalDateTime;

/**
 * 配租批次视图。
 */
public record BatchVO(
        Long id,
        String batchNo,
        String batchName,
        Long orgId,
        String securityType,
        String batchType,
        Integer houseCount,
        Integer applicantCount,
        LocalDateTime signupStart,
        LocalDateTime signupEnd,
        LocalDateTime lotteryTime,
        LocalDateTime selectStart,
        LocalDateTime selectEnd,
        String lotterySeed,
        String notaryInfo,
        String batchStatus,
        String batchStatusLabel,
        String remark,
        LocalDateTime createTime
) {
    public static BatchVO from(BizBatch e) {
        if (e == null) {
            return null;
        }
        BatchStatus st;
        try {
            st = BatchStatus.valueOf(e.getBatchStatus());
        } catch (IllegalArgumentException ex) {
            st = BatchStatus.DRAFT;
        }
        return new BatchVO(e.getId(), e.getBatchNo(), e.getBatchName(), e.getOrgId(),
                e.getSecurityType(), e.getBatchType(), e.getHouseCount(), e.getApplicantCount(),
                e.getSignupStart(), e.getSignupEnd(), e.getLotteryTime(), e.getSelectStart(),
                e.getSelectEnd(), e.getLotterySeed(), e.getNotaryInfo(), e.getBatchStatus(),
                st.label(), e.getRemark(), e.getCreateTime());
    }
}
'''

FILES['biz/dto/AllocationVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.AllocationStatus;
import com.yundao.bp.biz.entity.BizAllocation;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 配租单视图。
 */
public record AllocationVO(
        Long id,
        String allocationNo,
        Long batchId,
        Long personId,
        Long houseId,
        Long spaceId,
        String allocationType,
        LocalDate allocationDate,
        LocalDate planRentStart,
        LocalDate planRentEnd,
        String allocationStatus,
        String allocationStatusLabel,
        LocalDateTime lockExpireTime,
        /** 派生：距锁定到期的剩余小时（负数=已超时） */
        Long lockRemainHours,
        /** 派生：是否已超过锁定时间未签约 */
        Boolean lockOverdue,
        String giveUpReason,
        LocalDateTime createTime
) {
    public static AllocationVO from(BizAllocation e) {
        if (e == null) {
            return null;
        }
        AllocationStatus st;
        try {
            st = AllocationStatus.valueOf(e.getAllocationStatus());
        } catch (IllegalArgumentException ex) {
            st = AllocationStatus.PENDING_SIGN;
        }
        Long remain = null;
        boolean overdue = false;
        if (e.getLockExpireTime() != null) {
            remain = ChronoUnit.HOURS.between(LocalDateTime.now(), e.getLockExpireTime());
            overdue = st.holdsHouse() && remain < 0;
        }
        return new AllocationVO(e.getId(), e.getAllocationNo(), e.getBatchId(), e.getPersonId(),
                e.getHouseId(), e.getSpaceId(), e.getAllocationType(), e.getAllocationDate(),
                e.getPlanRentStart(), e.getPlanRentEnd(), e.getAllocationStatus(), st.label(),
                e.getLockExpireTime(), remain, overdue, e.getGiveUpReason(), e.getCreateTime());
    }
}
'''

FILES['biz/dto/LotteryResultVO.java'] = '''package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.LotteryResultType;
import com.yundao.bp.biz.entity.BizLotteryResult;
import java.time.LocalDateTime;

/**
 * 摇号结果视图。
 */
public record LotteryResultVO(
        Long id,
        Long batchId,
        Long personId,
        Long applicationId,
        Long waitingId,
        String resultType,
        String resultTypeLabel,
        String lotterySeq,
        Integer selectSeq,
        Long houseId,
        Long spaceId,
        LocalDateTime selectTime,
        String resultStatus,
        String giveUpReason
) {
    public static LotteryResultVO from(BizLotteryResult e) {
        if (e == null) {
            return null;
        }
        LotteryResultType t;
        try {
            t = LotteryResultType.valueOf(e.getResultType());
        } catch (IllegalArgumentException ex) {
            t = LotteryResultType.LOST;
        }
        return new LotteryResultVO(e.getId(), e.getBatchId(), e.getPersonId(),
                e.getApplicationId(), e.getWaitingId(), e.getResultType(), t.label(),
                e.getLotterySeq(), e.getSelectSeq(), e.getHouseId(), e.getSpaceId(),
                e.getSelectTime(), e.getResultStatus(), e.getGiveUpReason());
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
