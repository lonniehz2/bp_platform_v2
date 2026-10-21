# -*- coding: utf-8 -*-
"""生成报表/大屏/指标：实体 + Mapper + 服务 + 接口"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}


def entity(name, table, fields, doc, logic=False):
    li = 'import com.baomidou.mybatisplus.annotation.TableLogic;\n' if logic else ''
    lg = '\n    @TableLogic\n    private Integer isDeleted;\n' if logic else ''
    return f'''package com.yundao.bp.rpt.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
{li}import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Data;

/**
 * {doc}
 */
@Data
@TableName("{table}")
public class {name} {{

    @TableId(type = IdType.INPUT)
    private Long id;
{chr(10).join(fields)}
{lg}}}
'''


F['rpt/entity/RptReportDef.java'] = entity('RptReportDef', 'bp_rpt_report_def', [
    '    private String tenantId;',
    '    private String reportCode;',
    '    private String reportName;',
    '    /** HOUSE / PERSON / CONTRACT / FINANCE / DEVICE / WORKORDER */',
    '    private String reportType;',
    '    private String scenario;',
    '    /** 查询配置 JSON（数据源、字段、条件） */',
    '    private String queryConfig;',
    '    /** 列配置 JSON */',
    '    private String columnConfig;',
    '    /** EXCEL / CSV / PDF */',
    '    private String exportFormat;',
    '    private String reportStatus;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private LocalDateTime updateTime;',
], '报表定义。对应 `bp_rpt_report_def`。', True)

F['rpt/entity/RptExportTask.java'] = entity('RptExportTask', 'bp_rpt_export_task', [
    '    private String tenantId;',
    '    private String taskNo;',
    '    private String exportType;',
    '    private String reportCode;',
    '    private String queryParams;',
    '    private String fileName;',
    '    private String fileUrl;',
    '    private Long fileSize;',
    '    private Integer rowCount;',
    '    /** PENDING / RUNNING / SUCCESS / FAILED */',
    '    private String taskStatus;',
    '    private Integer progress;',
    '    private String failReason;',
    '    private LocalDateTime expireTime;',
    '    private Long userId;',
    '    private LocalDateTime createTime;',
    '    private LocalDateTime finishTime;',
], '导出任务。对应 `bp_rpt_export_task`。')

F['rpt/entity/RptMetricDaily.java'] = entity('RptMetricDaily', 'bp_rpt_metric_daily', [
    '    private String tenantId;',
    '    private LocalDate statDate;',
    '    private Long orgId;',
    '    private String metricCode;',
    '    private String metricName;',
    '    private BigDecimal metricValue;',
    '    private String metricUnit;',
    '    private String dimensionJson;',
    '    private LocalDateTime createTime;',
    '    private LocalDateTime updateTime;',
], '指标日汇总。对应 `bp_rpt_metric_daily`。')

F['rpt/entity/RptMetricHourly.java'] = entity('RptMetricHourly', 'bp_rpt_metric_hourly', [
    '    private String tenantId;',
    '    private LocalDateTime statHour;',
    '    private Long orgId;',
    '    private String metricCode;',
    '    private BigDecimal metricValue;',
    '    private LocalDateTime createTime;',
], '指标小时汇总。对应 `bp_rpt_metric_hourly`。')

F['rpt/entity/RptScreenDef.java'] = entity('RptScreenDef', 'bp_rpt_screen_def', [
    '    private String tenantId;',
    '    private String screenCode;',
    '    private String screenName;',
    '    /** OVERVIEW / HOUSE / PERSON / DEVICE / FINANCE */',
    '    private String screenType;',
    '    private String scenario;',
    '    /** 布局配置 JSON */',
    '    private String layoutConfig;',
    '    /** 组件配置 JSON（指标、图表类型、数据源） */',
    '    private String widgetConfig;',
    '    private Integer refreshSeconds;',
    '    private String screenStatus;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private LocalDateTime updateTime;',
], '大屏定义。对应 `bp_rpt_screen_def`。', True)

for n in ('RptReportDef', 'RptExportTask', 'RptMetricDaily', 'RptMetricHourly',
          'RptScreenDef'):
    F['rpt/mapper/%sMapper.java' % n] = f'''package com.yundao.bp.rpt.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.rpt.entity.{n};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {n}Mapper extends BaseMapper<{n}> {{
}}
'''

# ==================== DTO ====================
F['rpt/dto/ReportQueryCmd.java'] = '''package com.yundao.bp.rpt.dto;

import jakarta.validation.constraints.NotBlank;
import java.time.LocalDate;

/**
 * 报表查询 / 导出请求。
 */
public record ReportQueryCmd(

        @NotBlank(message = "报表编码不能为空")
        String reportCode,

        LocalDate dateFrom,
        LocalDate dateTo,

        Long orgId,

        /** 页码（直接查询时使用） */
        Integer pageNum,
        Integer pageSize,

        /** 导出格式覆盖：CSV / EXCEL */
        String exportFormat
) {
}
'''

F['rpt/dto/ReportResultVO.java'] = '''package com.yundao.bp.rpt.dto;

import java.util.List;
import java.util.Map;

/**
 * 报表查询结果。
 *
 * @param columns 列定义（key + title）
 * @param rows    数据行
 */
public record ReportResultVO(
        String reportCode,
        String reportName,
        List<Map<String, String>> columns,
        List<Map<String, Object>> rows,
        long total,
        String summary
) {
}
'''

F['rpt/dto/ExportTaskVO.java'] = '''package com.yundao.bp.rpt.dto;

import com.yundao.bp.rpt.entity.RptExportTask;
import java.time.LocalDateTime;

/**
 * 导出任务视图。
 */
public record ExportTaskVO(
        Long id,
        String taskNo,
        String exportType,
        String reportCode,
        String fileName,
        String fileUrl,
        Long fileSize,
        Integer rowCount,
        String taskStatus,
        Integer progress,
        String failReason,
        LocalDateTime expireTime,
        LocalDateTime createTime,
        LocalDateTime finishTime
) {
    public static ExportTaskVO from(RptExportTask e) {
        if (e == null) {
            return null;
        }
        return new ExportTaskVO(e.getId(), e.getTaskNo(), e.getExportType(), e.getReportCode(),
                e.getFileName(), e.getFileUrl(), e.getFileSize(), e.getRowCount(),
                e.getTaskStatus(), e.getProgress(), e.getFailReason(), e.getExpireTime(),
                e.getCreateTime(), e.getFinishTime());
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
