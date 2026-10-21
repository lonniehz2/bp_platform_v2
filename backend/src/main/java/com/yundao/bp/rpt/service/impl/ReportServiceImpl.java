package com.yundao.bp.rpt.service.impl;

import com.yundao.bp.common.util.EnumLabels;
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
                             @Value("${bp.rpt.export-dir:/var/lib/bp-export}") String exportDir) {
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
            // 导出格式：CSV（默认）或 EXCEL。Excel 用免依赖的 SpreadsheetML 2003（.xls），
            // Excel / WPS 均可直接打开，无需引入 POI 等重依赖。
            boolean excel = "EXCEL".equalsIgnoreCase(cmd.exportFormat());
            String content = excel ? toXls(cols, rows) : toCsv(cols, rows);
            Path dir = Path.of(exportDir);
            Files.createDirectories(dir);
            String fileName = def.getReportCode() + "-" + now.format(TS) + (excel ? ".xls" : ".csv");
            Path file = dir.resolve(fileName);
            byte[] all = excel
                    ? content.getBytes(StandardCharsets.UTF_8)
                    : withBom(content);
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
                    r.put("houseType", EnumLabels.of("HOUSE_TYPE", h.getHouseType()));
                    r.put("area", h.getArea());
                    r.put("houseStatus", EnumLabels.of("HOUSE_STATUS", h.getHouseStatus()));
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
                    r.put("contractStatus", EnumLabels.of("CONTRACT_STATUS", c.getContractStatus()));
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
                    r.put("billStatus", EnumLabels.of("BILL_STATUS", b.getBillStatus()));
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

    /** HTML 转义（用于 Excel XML 单元格文本） */
    private static String xmlEscape(String s) {
        if (s == null) {
            return "";
        }
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\"", "&quot;");
    }

    /**
     * 生成 Excel 可直接打开的表格：SpreadsheetML 2003（.xls）。
     *
     * <p>选择该格式是为了不引入 Apache POI 之类重依赖——
     * 本质是一段 XML，Excel / WPS / LibreOffice 都能正常打开且保留表格结构。
     */
    private static String toXls(List<Map<String, String>> cols, List<Map<String, Object>> rows) {
        StringBuilder sb = new StringBuilder(1024 + rows.size() * 128);
        sb.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
          .append("<?mso-application progid=\"Excel.Sheet\"?>\n")
          .append("<Workbook xmlns=\"urn:schemas-microsoft-com:office:spreadsheet\"")
          .append(" xmlns:ss=\"urn:schemas-microsoft-com:office:spreadsheet\">\n")
          .append("<Styles><Style ss:ID=\"h\"><Font ss:Bold=\"1\"/></Style></Styles>\n")
          .append("<Worksheet ss:Name=\"Sheet1\"><Table>\n");
        sb.append("<Row>");
        for (Map<String, String> c : cols) {
            sb.append("<Cell ss:StyleID=\"h\"><Data ss:Type=\"String\">")
              .append(xmlEscape(c.get("title"))).append("</Data></Cell>");
        }
        sb.append("</Row>\n");
        for (Map<String, Object> r : rows) {
            sb.append("<Row>");
            for (Map<String, String> c : cols) {
                Object v = r.get(c.get("key"));
                String text = v == null ? "" : String.valueOf(v);
                // 纯数字用 Number 类型，Excel 里可直接求和
                boolean num = text.matches("-?\\d+(\\.\\d+)?") && text.length() < 16;
                sb.append("<Cell><Data ss:Type=\"").append(num ? "Number" : "String")
                  .append("\">").append(xmlEscape(text)).append("</Data></Cell>");
            }
            sb.append("</Row>\n");
        }
        sb.append("</Table></Worksheet></Workbook>");
        return sb.toString();
    }

    /** CSV 加 UTF-8 BOM，Excel 打开中文不乱码 */
    private static byte[] withBom(String content) {
        byte[] bom = new byte[]{(byte) 0xEF, (byte) 0xBB, (byte) 0xBF};
        byte[] body = content.getBytes(StandardCharsets.UTF_8);
        byte[] all = new byte[bom.length + body.length];
        System.arraycopy(bom, 0, all, 0, bom.length);
        System.arraycopy(body, 0, all, bom.length, body.length);
        return all;
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
        sb.append('\n');
        for (Map<String, Object> r : rows) {
            for (int i = 0; i < cols.size(); i++) {
                if (i > 0) {
                    sb.append(',');
                }
                Object v = r.get(cols.get(i).get("key"));
                sb.append(escape(v == null ? "" : String.valueOf(v)));
            }
            sb.append('\n');
        }
        return sb.toString();
    }

    private static String escape(String s) {
        if (s == null) {
            return "";
        }
        if (s.contains(",") || s.contains("\"") || s.contains("\n")) {
            return "\"" + s.replace("\"", "\"\"") + "\"";
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
