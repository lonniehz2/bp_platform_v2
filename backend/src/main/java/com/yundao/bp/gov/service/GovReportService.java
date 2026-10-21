package com.yundao.bp.gov.service;

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
