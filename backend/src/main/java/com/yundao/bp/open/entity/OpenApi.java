package com.yundao.bp.open.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * 开放接口清单。对应 `bp_open_api`。
 */
@Data
@TableName("bp_open_api")
public class OpenApi {

    @TableId(type = IdType.INPUT)
    private Long id;
    private String apiCode;
    private String apiName;
    private String apiPath;
    private String httpMethod;
    /** HOUSE / PERSON / CONTRACT / ACCESS / ALERT / DEVICE */
    private String apiGroup;
    private Integer needAuth;
    private Integer rateLimit;
    private String apiStatus;
    private String description;
    private LocalDateTime createTime;
}
