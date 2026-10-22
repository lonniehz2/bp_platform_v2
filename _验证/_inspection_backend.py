# -*- coding: utf-8 -*-
"""物业巡检计划：按周期自动生成工单。

新增：
  · 表 bp_ops_inspection_plan（计划名/组织/空间/周期/下次执行/负责人/状态）
  · Service：创建、分页、到期执行（生成 INSPECTION 类工单并推进下次执行日）
  · Controller：POST/GET /ops/inspection-plans、POST /ops/inspection-plans/run-due
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'ops')

import pymysql

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = conn.cursor()
cur.execute("show tables like 'bp_ops_inspection_plan'")
if not cur.fetchone():
    cur.execute('''
        create table bp_ops_inspection_plan (
          id bigint not null primary key,
          tenant_id varchar(32) not null,
          org_id bigint null,
          space_id bigint null,
          plan_name varchar(128) not null,
          inspect_type varchar(32) not null comment 'SAFETY/EQUIPMENT/CLEANING/GREEN',
          frequency varchar(16) not null comment 'DAY/WEEK/MONTH',
          next_run_date date not null,
          assign_user_id bigint null,
          assign_user_name varchar(64) null,
          plan_status varchar(16) not null default 'ENABLED',
          remark varchar(255) null,
          create_by varchar(64) null,
          create_time datetime not null,
          update_time datetime null,
          is_deleted tinyint not null default 0,
          key idx_plan_due (tenant_id, plan_status, next_run_date)
        ) comment '物业巡检计划'
    ''')
    conn.commit()
    print('表 bp_ops_inspection_plan 已创建')
else:
    print('表已存在')
conn.close()

# ---------- 实体 ----------
io.open(os.path.join(J, 'entity', 'OpsInspectionPlan.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.ops.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/** 物业巡检计划（按周期自动生成工单）。 */
@Data
@TableName("bp_ops_inspection_plan")
public class OpsInspectionPlan {

    @TableId(type = IdType.INPUT)
    private Long id;

    private String tenantId;
    private Long orgId;
    private Long spaceId;
    private String planName;

    /** SAFETY / EQUIPMENT / CLEANING / GREEN */
    private String inspectType;

    /** DAY / WEEK / MONTH */
    private String frequency;

    private LocalDate nextRunDate;
    private Long assignUserId;
    private String assignUserName;
    private String planStatus;
    private String remark;
    private String createBy;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    private Integer isDeleted;
}
''')

io.open(os.path.join(J, 'mapper', 'OpsInspectionPlanMapper.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.ops.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.ops.entity.OpsInspectionPlan;
import org.apache.ibatis.annotations.Mapper;

/** 巡检计划 Mapper。 */
@Mapper
public interface OpsInspectionPlanMapper extends BaseMapper<OpsInspectionPlan> {
}
''')

# ---------- DTO ----------
io.open(os.path.join(J, 'dto', 'InspectionPlanCmd.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.ops.dto;

import jakarta.validation.constraints.NotBlank;
import java.time.LocalDate;

/**
 * 新建巡检计划。
 *
 * @param frequency DAY/WEEK/MONTH
 * @param nextRunDate 首次执行日（空则按今天）
 */
public record InspectionPlanCmd(
        String planName,
        Long orgId,
        Long spaceId,
        String inspectType,
        String frequency,
        LocalDate nextRunDate,
        Long assignUserId,
        String assignUserName,
        String remark) {
}
''')

# ---------- Service ----------
io.open(os.path.join(J, 'service', 'InspectionPlanService.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.InspectionPlanCmd;
import com.yundao.bp.ops.entity.OpsInspectionPlan;
import java.util.Map;

/** 巡检计划服务。 */
public interface InspectionPlanService {

    OpsInspectionPlan create(InspectionPlanCmd cmd);

    PageResult<OpsInspectionPlan> page(long pageNum, long pageSize, String planStatus);

    /** 执行到期计划：生成工单并推进下次执行日，返回 {generated, skipped}。 */
    Map<String, Object> runDue();
}
''')

io.open(os.path.join(J, 'service', 'impl', 'InspectionPlanServiceImpl.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.ops.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.util.SnowflakeIdGenerator;
import com.yundao.bp.ops.dto.InspectionPlanCmd;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.entity.OpsInspectionPlan;
import com.yundao.bp.ops.mapper.OpsInspectionPlanMapper;
import com.yundao.bp.ops.service.InspectionPlanService;
import com.yundao.bp.ops.service.WorkOrderService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 巡检计划实现：按周期生成工单。 */
@Service
public class InspectionPlanServiceImpl implements InspectionPlanService {

    private static final Logger log = LoggerFactory.getLogger(InspectionPlanServiceImpl.class);

    private final OpsInspectionPlanMapper mapper;
    private final SnowflakeIdGenerator idGen;
    private final WorkOrderService workOrderService;

    public InspectionPlanServiceImpl(OpsInspectionPlanMapper mapper, SnowflakeIdGenerator idGen,
                                     WorkOrderService workOrderService) {
        this.mapper = mapper;
        this.idGen = idGen;
        this.workOrderService = workOrderService;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OpsInspectionPlan create(InspectionPlanCmd cmd) {
        if (cmd.planName() == null || cmd.planName().isBlank()) {
            throw BizException.paramInvalid("计划名称不能为空");
        }
        OpsInspectionPlan p = new OpsInspectionPlan();
        p.setId(idGen.nextId());
        p.setTenantId(TenantContext.tenantId());
        p.setOrgId(cmd.orgId());
        p.setSpaceId(cmd.spaceId());
        p.setPlanName(cmd.planName());
        p.setInspectType(cmd.inspectType() == null ? "SAFETY" : cmd.inspectType());
        p.setFrequency(cmd.frequency() == null ? "WEEK" : cmd.frequency());
        p.setNextRunDate(cmd.nextRunDate() == null ? LocalDate.now() : cmd.nextRunDate());
        p.setAssignUserId(cmd.assignUserId());
        p.setAssignUserName(cmd.assignUserName());
        p.setPlanStatus("ENABLED");
        p.setRemark(cmd.remark());
        p.setIsDeleted(0);
        p.setCreateTime(LocalDateTime.now());
        mapper.insert(p);
        return p;
    }

    @Override
    public PageResult<OpsInspectionPlan> page(long pageNum, long pageSize, String planStatus) {
        LambdaQueryWrapper<OpsInspectionPlan> qw = new LambdaQueryWrapper<OpsInspectionPlan>()
                .eq(planStatus != null && !planStatus.isBlank(),
                        OpsInspectionPlan::getPlanStatus, planStatus)
                .orderByAsc(OpsInspectionPlan::getNextRunDate);
        var page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> runDue() {
        LocalDate today = LocalDate.now();
        List<OpsInspectionPlan> due = mapper.selectList(
                new LambdaQueryWrapper<OpsInspectionPlan>()
                        .eq(OpsInspectionPlan::getPlanStatus, "ENABLED")
                        .le(OpsInspectionPlan::getNextRunDate, today));
        int generated = 0;
        int skipped = 0;
        for (OpsInspectionPlan p : due) {
            try {
                WorkOrderCreateCmd cmd = new WorkOrderCreateCmd(
                        "INSPECTION", "PLAN",
                        "巡检任务：" + p.getPlanName(),
                        "巡检类型 " + p.getInspectType() + "，周期 " + p.getFrequency(),
                        p.getOrgId(), p.getSpaceId(), null, null, null,
                        p.getAssignUserId(), p.getAssignUserName(), null, null);
                workOrderService.create(cmd);
                p.setNextRunDate(advance(p.getNextRunDate(), p.getFrequency()));
                p.setUpdateTime(LocalDateTime.now());
                mapper.updateById(p);
                generated++;
            } catch (Exception ex) {
                log.warn("巡检计划 {} 生成工单失败：{}", p.getId(), ex.getMessage());
                skipped++;
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("due", due.size());
        out.put("generated", generated);
        out.put("skipped", skipped);
        return out;
    }

    /** 推进下次执行日。 */
    private LocalDate advance(LocalDate base, String frequency) {
        String f = frequency == null ? "WEEK" : frequency;
        LocalDate next = switch (f) {
            case "DAY" -> base.plusDays(1);
            case "MONTH" -> base.plusMonths(1);
            default -> base.plusWeeks(1);
        };
        LocalDate today = LocalDate.now();
        while (!next.isAfter(today)) {
            next = advance(next, f);
        }
        return next;
    }
}
''')

# ---------- Controller ----------
io.open(os.path.join(J, 'controller', 'InspectionPlanController.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.ops.dto.InspectionPlanCmd;
import com.yundao.bp.ops.entity.OpsInspectionPlan;
import com.yundao.bp.ops.service.InspectionPlanService;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 物业巡检计划。 */
@RestController
@RequestMapping("/api/v1/ops/inspection-plans")
public class InspectionPlanController {

    private final InspectionPlanService service;

    public InspectionPlanController(InspectionPlanService service) {
        this.service = service;
    }

    @PostMapping
    @RequirePerm("ops:workorder:create")
    public R<OpsInspectionPlan> create(@Valid @RequestBody InspectionPlanCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @GetMapping
    @RequirePerm("ops:workorder:view")
    public R<PageResult<OpsInspectionPlan>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String planStatus) {
        return R.ok(service.page(pageNum, pageSize, planStatus));
    }

    /** 手动触发到期巡检：为到期的计划生成工单。 */
    @PostMapping("/run-due")
    @RequirePerm("ops:workorder:create")
    public R<Map<String, Object>> runDue() {
        return R.ok(service.runDue());
    }
}
''')
print('巡检计划 后端已生成（实体/Mapper/DTO/Service/Controller）')
