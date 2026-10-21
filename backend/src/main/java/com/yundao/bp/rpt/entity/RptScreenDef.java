package com.yundao.bp.rpt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableLogic;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 大屏定义。对应 `bp_rpt_screen_def`。
 */
@Data
@TableName("bp_rpt_screen_def")
public class RptScreenDef {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String tenantId;
    private String screenCode;
    private String screenName;
    /** OVERVIEW / HOUSE / PERSON / DEVICE / FINANCE */
    private String screenType;
    private String scenario;
    /** 布局配置 JSON */
    private String layoutConfig;
    /** 组件配置 JSON（指标、图表类型、数据源） */
    private String widgetConfig;
    private Integer refreshSeconds;
    private String screenStatus;
    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    @TableLogic
    private Integer isDeleted;
}
