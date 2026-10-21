# -*- coding: utf-8 -*-
"""生成监管报送（4 表）+ 开放平台/报送 控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}


def ent(pkg, name, table, fields, doc, extra_imports=''):
    return f'''package com.yundao.bp.{pkg}.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;
{extra_imports}
/**
 * {doc}
 */
@Data
@TableName("{table}")
public class {name} {{

    @TableId(type = IdType.INPUT)
    private Long id;
{chr(10).join(fields)}
}}
'''


F['gov/entity/GovAdapterConfig.java'] = ent('gov', 'GovAdapterConfig', 'bp_gov_adapter_config', [
    '    private String tenantId;',
    '    private String adapterCode;',
    '    private String adapterName;',
    '    /** PUBLIC_HOUSING / POLICE / HOUSING / REAL_ESTATE */',
    '    private String systemType;',
    '    /** HTTP / WEBSOCKET / FILE / SFTP / DB */',
    '    private String protocol;',
    '    private String endpoint;',
    '    /** NONE / APPKEY / TOKEN / BASIC / CERT / SIGN */',
    '    private String authType;',
    '    /** 鉴权配置 JSON（敏感，不对外返回） */',
    '    private String authConfig;',
    '    private Integer timeoutMs;',
    '    private Integer retryTimes;',
    '    private Integer qpsLimit;',
    '    /** RETRY / MANUAL / FILE / BLOCK */',
    '    private String degradeMode;',
    '    /** ENABLED / DISABLED */',
    '    private String adapterStatus;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private String updateBy;',
    '    private LocalDateTime updateTime;',
], '政务系统适配器配置。对应 `bp_gov_adapter_config`。')

F['gov/entity/GovAdapterLog.java'] = ent('gov', 'GovAdapterLog', 'bp_gov_adapter_log', [
    '    private String tenantId;',
    '    private String adapterCode;',
    '    private String traceId;',
    '    private String bizType;',
    '    private Long bizId;',
    '    private String requestBody;',
    '    private String responseBody;',
    '    private Integer successFlag;',
    '    private String errorMsg;',
    '    private Integer durationMs;',
    '    private LocalDateTime callTime;',
    '    private LocalDateTime createTime;',
], '政务适配器调用日志。对应 `bp_gov_adapter_log`。')

F['gov/entity/GovReportTask.java'] = ent('gov', 'GovReportTask', 'bp_gov_report_task', [
    '    private String tenantId;',
    '    private String taskNo;',
    '    /** PUBLIC_HOUSING / POLICE / HOUSING / REAL_ESTATE */',
    '    private String targetSystem;',
    '    /** HOUSE / TENANT / STATUS / CONTRACT / FINANCE / ACCESS */',
    '    private String reportType;',
    '    /** API / FILE / MANUAL */',
    '    private String reportMode;',
    '    /** REALTIME / DAILY / MONTHLY / QUARTERLY / ONCE */',
    '    private String reportCycle;',
    '    /** 数据范围 JSON（时间跨度/组织范围） */',
    '    private String dataRange;',
    '    private Integer recordCount;',
    '    private Integer successCount;',
    '    private Integer failCount;',
    '    private String fileUrl;',
    '    /** PENDING / RUNNING / SUCCESS / PARTIAL / FAILED */',
    '    private String taskStatus;',
    '    private String failDetail;',
    '    private LocalDateTime reportTime;',
    '    private String createBy;',
    '    private LocalDateTime createTime;',
    '    private LocalDateTime updateTime;',
], '监管报送任务。对应 `bp_gov_report_task`。')

F['gov/entity/GovReportDetail.java'] = ent('gov', 'GovReportDetail', 'bp_gov_report_detail', [
    '    private String tenantId;',
    '    private Long taskId;',
    '    private String bizType;',
    '    private Long bizId;',
    '    /** 外部系统 ID（回写，便于对账） */',
    '    private String externalId;',
    '    /** PENDING / SUCCESS / FAILED / SKIPPED */',
    '    private String syncStatus;',
    '    private String errorCode;',
    '    private String errorMsg;',
    '    private String requestData;',
    '    private String responseData;',
    '    private LocalDateTime createTime;',
], '监管报送明细。对应 `bp_gov_report_detail`。')

for n in ('GovAdapterConfig', 'GovAdapterLog', 'GovReportTask', 'GovReportDetail'):
    F['gov/mapper/%sMapper.java' % n] = f'''package com.yundao.bp.gov.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yundao.bp.gov.entity.{n};
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface {n}Mapper extends BaseMapper<{n}> {{
}}
'''

# ==================== 报送服务 ====================
F['gov/service/GovReportService.java'] = '''package com.yundao.bp.gov.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.gov.entity.GovAdapterConfig;
import com.yundao.bp.gov.entity.GovReportDetail;
import com.yundao.bp.gov.entity.GovReportTask;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 监管报送服务。
 *
 * <p><b>设计要点</b>：
 * <ul>
 *   <li><b>适配器隔离</b>：不同地区房管局接口不同，用 {@code adapter_code} 隔离，
 *       不写 if/else 分支</li>
 *   <li><b>任务+明细双层</b>：任务记汇总（成功/失败数），明细记每条记录的
 *       请求快照与外部 ID，便于「部分成功」后精确补报</li>
 *   <li><b>降级策略可配</b>：RETRY / MANUAL / FILE / BLOCK，政务系统不可用时
 *       不能把业务卡死</li>
 * </ul>
 */
public interface GovReportService {

    /** 适配器配置列表（鉴权配置脱敏）。 */
    List<GovAdapterConfig> listAdapters();

    GovAdapterConfig saveAdapter(String adapterCode, String adapterName, String systemType,
                                 String protocol, String endpoint, String authType,
                                 String degradeMode);

    /**
     * 生成并执行报送任务。
     *
     * @param targetSystem 目标系统
     * @param reportType   HOUSE / TENANT / CONTRACT
     * @param dateFrom     数据范围开始（可为空）
     * @param dateTo       数据范围结束（可为空）
     * @return 任务（含成功/失败明细统计）
     */
    GovReportTask submit(String targetSystem, String reportType, LocalDate dateFrom,
                         LocalDate dateTo, String operator);

    GovReportTask getTask(Long id);

    List<GovReportDetail> taskDetails(Long taskId);

    PageResult<GovReportTask> pageTasks(long pageNum, long pageSize, String targetSystem,
                                        String reportType, String taskStatus);

    /**
     * 重试失败明细（部分成功后的补报）。
     *
     * @return 本次成功条数
     */
    int retryFailed(Long taskId);

    /** 报送统计（监管看板）。 */
    Map<String, Object> stats(LocalDate dateFrom, LocalDate dateTo);
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
