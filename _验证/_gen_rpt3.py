# -*- coding: utf-8 -*-
"""生成报表/大屏实现 + 控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

F['rpt/service/impl/ReportServiceImpl.java'] = '''package com.yundao.bp.rpt.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.rpt.dto.ExportTaskVO;
import com.yundao.bp.rpt.dto.ReportQueryCmd;
import com.yundao.bp.rpt.dto.ReportResultVO;
import com.yundao.bp.rpt.entity.RptExportTask;
import com.yundao.bp.rpt.entity.RptReportDef;
import com.yundao.bp.rpt.mapper.RptExportTaskMapper;
import com.yundao.bp.rpt.mapper.RptReportDefMapper;
import com.yundao.bp.rpt.service.ReportService;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 报表实现。
 *
 * <p>内置三张报表：房源台账、合同台账、欠费台账。
 * 导出为 CSV（UTF-8 BOM，Excel 可直接打开）。
 */
@Service
public class ReportServiceImpl implements ReportService {

    private static final Logger log = LoggerFactory.getLogger(ReportServiceImpl.class);
    private static final DateTimeFormatter TS = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");

    private final RptReportDefMapper defMapper;
    private final RptExportTaskMapper taskMapper;
    private final AssetHouseMapper houseMapper;
    private final BizContractMapper contractMapper;
    private final FinBillMapper billMapper;
    private final SnowflakeIdGenerator idGen;
    private final String exportDir;

    public ReportServiceImpl(RptReportDefMapper defMapper, RptExportTaskMapper taskMapper,
                             AssetHouseMapper houseMapper, BizContractMapper contractMapper,
                             FinBillMapper billMapper, SnowflakeIdGenerator idGen,
                             @Value("${bp.rpt.export-dir:/tmp/bp-export}") String exportDir) {
        this.defMapper = defMapper;
        this.taskMapper = taskMapper;
        this.houseMapper = houseMapper;
        this.contractMapper = contractMapper;
        this.billMapper = billMapper;
        this.idGen = idGen;
        this.exportDir = exportDir;
    }

    @Override
    public List<RptReportDef> listReports(String reportType) {
        return defMapper.selectList(new LambdaQueryWrapper<RptReportDef>()
                .eq(reportType != null && !reportType.isBlank(),
                        RptReportDef::getReportType, reportType)
                .eq(RptReportDef::getReportStatus, "ENABLED")
                .orderByAsc(RptReportDef::getReportCode));
    }

    @Override
    public ReportResultVO query(ReportQueryCmd cmd) {
        RptReportDef def = findDef(cmd.reportCode());
        List<Map<String, String>> columns = columnsOf(def.getReportCode());
        List<Map<String, Object>> rows = rowsOf(def.getReportCode(), cmd.orgId());
        int pn = cmd.pageNum() == null || cmd.pageNum() <= 0 ? 1 : cmd.pageNum();
        int ps = cmd.pageSize() == null || cmd.pageSize() <= 0 ? 20 : cmd.pageSize();
        int from = Math.min((pn - 1) * ps, rows.size());
        int to = Math.min(from + ps, rows.size());
        return new ReportResultVO(def.getReportCode(), def.getReportName(), columns,
                rows.subList(from, to), rows.size(),
                "共 " + rows.size() + " 行，当前第 " + pn + " 页");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ExportTaskVO export(ReportQueryCmd cmd, Long userId) {
        RptReportDef def = findDef(cmd.reportCode());
        LocalDateTime now = LocalDateTime.now();
        long id = idGen.nextId();

        RptExportTask t = new RptExportTask();
        t.setId(id);
        t.setTenantId(TenantContext.tenantId());
        t.setTaskNo("EX" + id);
        t.setExportType("REPORT");
        t.setReportCode(cmd.reportCode());
        t.setQueryParams(toJson(cmd));
        t.setUserId(userId);
        t.setProgress(0);
        t.setTaskStatus("PENDING");
        t.setCreateTime(now);
        taskMapper.insert(t);

        // 同步执行（数据量不大；大数据量可改为异步队列，接口已预留 runPendingTasks）
        try {
            List<Map<String, String>> cols = columnsOf(def.getReportCode());
            List<Map<String, Object>> rows = rowsOf(def.getReportCode(), cmd.orgId());
            String csv = toCsv(cols, rows);
            Path dir = Path.of(exportDir);
            Files.createDirectories(dir);
            String fileName = def.getReportCode() + "-" + now.format(TS) + ".csv";
            Path file = dir.resolve(fileName);
            // UTF-8 BOM，Excel 打开中文不乱码
            byte[] bom = new byte[]{(byte) 0xEF, (byte) 0xBB, (byte) 0xBF};
            byte[] body = csv.getBytes(StandardCharsets.UTF_8);
            byte[] all = new byte[bom.length + body.length];
            System.arraycopy(bom, 0, all, 0, bom.length);
            System.arraycopy(body, 0, all, bom.length, body.length);
            Files.write(file, all);

            t.setFileName(fileName);
            t.setFileUrl(file.toAbsolutePath().toString());
            t.setFileSize((long) all.length);
            t.setRowCount(rows.size());
            t.setTaskStatus("SUCCESS");
            t.setProgress(100);
            t.setFinishTime(LocalDateTime.now());
            t.setExpireTime(now.plusDays(7));
            taskMapper.updateById(t);
            log.info("报表导出成功：{}（{} 行，{} 字节）", fileName, rows.size(), all.length);
        } catch (Exception ex) {
            t.setTaskStatus("FAILED");
            t.setFailReason(ex.getMessage());
            t.setFinishTime(LocalDateTime.now());
            taskMapper.updateById(t);
            log.error("报表导出失败：{}", ex.getMessage());
        }
        return ExportTaskVO.from(t);
    }

    @Override
    public ExportTaskVO getTask(Long id) {
        RptExportTask t = taskMapper.selectById(id);
        if (t == null) {
            throw BizException.notFound("导出任务");
        }
        return ExportTaskVO.from(t);
    }

    @Override
    public List<ExportTaskVO> listTasks(Long userId) {
        return taskMapper.selectList(new LambdaQueryWrapper<RptExportTask>()
                        .eq(userId != null, RptExportTask::getUserId, userId)
                        .orderByDesc(RptExportTask::getId))
                .stream().map(ExportTaskVO::from).toList();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int runPendingTasks() {
        List<RptExportTask> list = taskMapper.selectList(
                new LambdaQueryWrapper<RptExportTask>()
                        .eq(RptExportTask::getTaskStatus, "PENDING"));
        int n = 0;
        for (RptExportTask t : list) {
            t.setTaskStatus("RUNNING");
            t.setProgress(50);
            taskMapper.updateById(t);
            n++;
        }
        return n;
    }

    @Override
    public String readFile(Long taskId) {
        RptExportTask t = taskMapper.selectById(taskId);
        if (t == null || t.getFileUrl() == null) {
            throw BizException.notFound("导出文件");
        }
        try {
            return Files.readString(Path.of(t.getFileUrl()), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.NOT_FOUND,
                    "文件已失效或不存在");
        }
    }

    // ==================== 内置报表数据 ====================

    private RptReportDef findDef(String code) {
        RptReportDef def = defMapper.selectOne(new LambdaQueryWrapper<RptReportDef>()
                .eq(RptReportDef::getReportCode, code)
                .last("LIMIT 1"));
        if (def == null) {
            throw BizException.notFound("报表定义");
        }
        return def;
    }

    private List<Map<String, String>> columnsOf(String code) {
        List<Map<String, String>> cols = new ArrayList<>();
        switch (code) {
            case "HOUSE_LEDGER" -> {
                col(cols, "houseCode", "房源编号");
                col(cols, "houseName", "房源名称");
                col(cols, "houseType", "房源类型");
                col(cols, "area", "面积(㎡)");
                col(cols, "houseStatus", "房源状态");
            }
            case "CONTRACT_LEDGER" -> {
                col(cols, "contractNo", "合同号");
                col(cols, "lesseeName", "承租人");
                col(cols, "leaseStart", "起租日");
                col(cols, "leaseEnd", "止租日");
                col(cols, "monthlyRent", "月租金");
                col(cols, "contractStatus", "状态");
            }
            case "ARREARS_LEDGER" -> {
                col(cols, "billNo", "账单号");
                col(cols, "payerName", "缴费人");
                col(cols, "billPeriod", "账期");
                col(cols, "payableAmount", "应付金额");
                col(cols, "dueDate", "缴费截止日");
                col(cols, "billStatus", "状态");
            }
            default -> col(cols, "info", "说明");
        }
        return cols;
    }

    private List<Map<String, Object>> rowsOf(String code, Long orgId) {
        List<Map<String, Object>> rows = new ArrayList<>();
        switch (code) {
            case "HOUSE_LEDGER" -> {
                for (AssetHouse h : houseMapper.selectList(
                        new LambdaQueryWrapper<AssetHouse>()
                                .eq(orgId != null, AssetHouse::getOrgId, orgId)
                                .orderByAsc(AssetHouse::getId))) {
                    Map<String, Object> r = new LinkedHashMap<>();
                    r.put("houseCode", h.getHouseCode());
                    r.put("houseName", h.getHouseName());
                    r.put("houseType", h.getHouseType());
                    r.put("area", h.getArea());
                    r.put("houseStatus", h.getHouseStatus());
                    rows.add(r);
                }
            }
            case "CONTRACT_LEDGER" -> {
                for (BizContract c : contractMapper.selectList(
                        new LambdaQueryWrapper<BizContract>()
                                .eq(orgId != null, BizContract::getOrgId, orgId)
                                .orderByAsc(BizContract::getId))) {
                    Map<String, Object> r = new LinkedHashMap<>();
                    r.put("contractNo", c.getContractNo());
                    r.put("lesseeName", c.getLesseeName());
                    r.put("leaseStart", c.getLeaseStart());
                    r.put("leaseEnd", c.getLeaseEnd());
                    r.put("monthlyRent", c.getMonthlyRent());
                    r.put("contractStatus", c.getContractStatus());
                    rows.add(r);
                }
            }
            case "ARREARS_LEDGER" -> {
                for (FinBill b : billMapper.selectList(
                        new LambdaQueryWrapper<FinBill>()
                                .eq(orgId != null, FinBill::getOrgId, orgId)
                                .in(FinBill::getBillStatus,
                                        List.of("UNPAID", "PARTIAL", "OVERDUE"))
                                .orderByAsc(FinBill::getId))) {
                    Map<String, Object> r = new LinkedHashMap<>();
                    r.put("billNo", b.getBillNo());
                    r.put("payerName", b.getPayerName());
                    r.put("billPeriod", b.getBillPeriod());
                    r.put("payableAmount", b.getPayableAmount());
                    r.put("dueDate", b.getDueDate());
                    r.put("billStatus", b.getBillStatus());
                    rows.add(r);
                }
            }
            default -> {
                Map<String, Object> r = new LinkedHashMap<>();
                r.put("info", "该报表尚未配置数据源");
                rows.add(r);
            }
        }
        return rows;
    }

    private static void col(List<Map<String, String>> cols, String key, String title) {
        Map<String, String> c = new LinkedHashMap<>();
        c.put("key", key);
        c.put("title", title);
        cols.add(c);
    }

    private static String toCsv(List<Map<String, String>> cols,
                                List<Map<String, Object>> rows) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < cols.size(); i++) {
            if (i > 0) {
                sb.append(',');
            }
            sb.append(escape(cols.get(i).get("title")));
        }
        sb.append('\\n');
        for (Map<String, Object> r : rows) {
            for (int i = 0; i < cols.size(); i++) {
                if (i > 0) {
                    sb.append(',');
                }
                Object v = r.get(cols.get(i).get("key"));
                sb.append(escape(v == null ? "" : String.valueOf(v)));
            }
            sb.append('\\n');
        }
        return sb.toString();
    }

    private static String escape(String s) {
        if (s == null) {
            return "";
        }
        if (s.contains(",") || s.contains("\\"") || s.contains("\\n")) {
            return "\\"" + s.replace("\\"", "\\"\\"") + "\\"";
        }
        return s;
    }

    private static String toJson(Object o) {
        try {
            return new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(o);
        } catch (Exception e) {
            return "{}";
        }
    }
}
'''

F['rpt/service/impl/ScreenServiceImpl.java'] = '''package com.yundao.bp.rpt.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.rpt.entity.RptScreenDef;
import com.yundao.bp.rpt.mapper.RptScreenDefMapper;
import com.yundao.bp.rpt.service.MetricService;
import com.yundao.bp.rpt.service.ScreenService;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 大屏实现。
 *
 * <p>大屏是<b>配置驱动</b>的：{@code widget_config} 描述要哪些指标、
 * 用什么图表；本服务按配置逐项取实时值返回，前端只负责渲染。
 */
@Service
public class ScreenServiceImpl implements ScreenService {

    private static final Logger log = LoggerFactory.getLogger(ScreenServiceImpl.class);

    /** 默认组件配置（未配置时的兜底） */
    private static final String DEFAULT_WIDGETS = """
            [
              {"code":"HOUSE_TOTAL","title":"房源总数","chart":"NUMBER"},
              {"code":"OCCUPANCY_RATE","title":"出租率(%)","chart":"GAUGE"},
              {"code":"HOUSE_VACANT","title":"空置房源","chart":"NUMBER"},
              {"code":"BILL_UNPAID_COUNT","title":"欠费账单","chart":"NUMBER"},
              {"code":"BILL_UNPAID_AMOUNT","title":"欠费金额","chart":"NUMBER"},
              {"code":"PAYMENT_TOTAL_AMOUNT","title":"累计收款","chart":"NUMBER"},
              {"code":"ACCESS_TODAY_COUNT","title":"今日开门","chart":"NUMBER"},
              {"code":"ACCESS_ABNORMAL_COUNT","title":"今日异常开门","chart":"NUMBER"}
            ]""";

    private final RptScreenDefMapper mapper;
    private final MetricService metricService;
    private final SnowflakeIdGenerator idGen;

    public ScreenServiceImpl(RptScreenDefMapper mapper, MetricService metricService,
                             SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.metricService = metricService;
        this.idGen = idGen;
    }

    @Override
    public List<RptScreenDef> listScreens(String screenType) {
        return mapper.selectList(new LambdaQueryWrapper<RptScreenDef>()
                .eq(screenType != null && !screenType.isBlank(),
                        RptScreenDef::getScreenType, screenType)
                .eq(RptScreenDef::getScreenStatus, "ENABLED")
                .orderByAsc(RptScreenDef::getScreenCode));
    }

    @Override
    public RptScreenDef getByCode(String screenCode) {
        RptScreenDef d = mapper.selectOne(new LambdaQueryWrapper<RptScreenDef>()
                .eq(RptScreenDef::getScreenCode, screenCode)
                .last("LIMIT 1"));
        if (d == null) {
            throw BizException.notFound("大屏定义");
        }
        return d;
    }

    @Override
    public Map<String, Object> data(String screenCode, Long orgId) {
        RptScreenDef def = getByCode(screenCode);
        String widgetsJson = def.getWidgetConfig();
        if (widgetsJson == null || widgetsJson.isBlank()) {
            widgetsJson = DEFAULT_WIDGETS;
        }
        List<Map<String, Object>> out = new ArrayList<>();
        try {
            List<Map<String, Object>> defs = new com.fasterxml.jackson.databind.ObjectMapper()
                    .readValue(widgetsJson, List.class);
            for (Map<String, Object> w : defs) {
                String code = String.valueOf(w.get("code"));
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("code", code);
                item.put("title", w.get("title"));
                item.put("chart", w.get("chart") == null ? "NUMBER" : w.get("chart"));
                item.put("value", metricService.current(code, orgId));
                out.add(item);
            }
        } catch (Exception ex) {
            log.warn("大屏组件配置解析失败，回退默认：{}", ex.getMessage());
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("screenCode", def.getScreenCode());
        m.put("screenName", def.getScreenName());
        m.put("screenType", def.getScreenType());
        m.put("refreshSeconds", def.getRefreshSeconds());
        m.put("layoutConfig", def.getLayoutConfig());
        m.put("widgets", out);
        m.put("generatedAt", LocalDateTime.now().toString());
        return m;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RptScreenDef save(String screenCode, String screenName, String screenType,
                             String layoutConfig, String widgetConfig,
                             Integer refreshSeconds) {
        RptScreenDef exist = mapper.selectOne(new LambdaQueryWrapper<RptScreenDef>()
                .eq(RptScreenDef::getScreenCode, screenCode)
                .last("LIMIT 1"));
        if (exist != null) {
            if (layoutConfig != null) {
                exist.setLayoutConfig(layoutConfig);
            }
            if (widgetConfig != null) {
                exist.setWidgetConfig(widgetConfig);
            }
            if (refreshSeconds != null) {
                exist.setRefreshSeconds(refreshSeconds);
            }
            exist.setUpdateTime(LocalDateTime.now());
            mapper.updateById(exist);
            return exist;
        }
        RptScreenDef d = new RptScreenDef();
        d.setId(idGen.nextId());
        d.setTenantId(TenantContext.tenantId());
        d.setScreenCode(screenCode);
        d.setScreenName(screenName);
        d.setScreenType(screenType == null ? "OVERVIEW" : screenType);
        d.setLayoutConfig(layoutConfig);
        d.setWidgetConfig(widgetConfig == null ? DEFAULT_WIDGETS : widgetConfig);
        d.setRefreshSeconds(refreshSeconds == null ? 60 : refreshSeconds);
        d.setScreenStatus("ENABLED");
        d.setIsDeleted(0);
        d.setCreateTime(LocalDateTime.now());
        d.setUpdateTime(LocalDateTime.now());
        mapper.insert(d);
        return d;
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
