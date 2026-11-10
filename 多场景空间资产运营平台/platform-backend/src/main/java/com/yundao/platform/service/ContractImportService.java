package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class ContractImportService {

    private final JdbcTemplate jdbc;
    private final GuaranteeContractService contractService;

    public ContractImportService(JdbcTemplate jdbc, GuaranteeContractService contractService) {
        this.jdbc = jdbc;
        this.contractService = contractService;
    }

    public Map<String, Object> importCsv(MultipartFile file) {
        if (file == null || file.isEmpty()) throw BizException.param("请上传 CSV 文件");
        String tenant = TenantContext.require();
        Map<String, Long> projects = new HashMap<>();
        for (Map<String, Object> row : jdbc.queryForList("select id, org_code orgCode from bp_org where tenant_id=? and is_deleted=0", tenant)) {
            projects.put(String.valueOf(row.get("orgCode")), ((Number) row.get("id")).longValue());
        }
        List<Map<String, Object>> errors = new ArrayList<>();
        int total = 0, success = 0;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {
            String line; int lineNo = 0;
            while ((line = reader.readLine()) != null) {
                lineNo++;
                line = line.replace("\ufeff", "");
                if (line.isBlank() || line.startsWith("#")) continue;
                if (lineNo == 1 && (line.contains("项目编码") || line.toLowerCase().contains("projectcode"))) continue;
                total++;
                String[] c = split(line);
                if (c.length < 7) { errors.add(err(lineNo, "列数不足，至少需要项目、合同号、房屋、人员、开始、结束、租金")); continue; }
                try {
                    String projectCode = v(c, 0); String contractNo = v(c, 1); String houseCode = v(c, 2); String personCode = v(c, 3);
                    Long projectId = projects.get(projectCode);
                    if (projectId == null) throw new IllegalArgumentException("项目编码不存在：" + projectCode);
                    Map<String, Object> house = jdbc.queryForMap("select id from bp_house where tenant_id=? and org_id=? and house_code=? and is_deleted=0", tenant, projectId, houseCode);
                    Map<String, Object> person = jdbc.queryForMap("select id from bp_person where tenant_id=? and person_code=? and is_deleted=0", tenant, personCode);
                    contractService.create(new GuaranteeContractService.ContractCmd(projectId, contractNo,
                            ((Number) house.get("id")).longValue(), ((Number) person.get("id")).longValue(),
                            LocalDate.parse(v(c, 4)), LocalDate.parse(v(c, 5)), decimal(v(c, 6)), decimal(v(c, 7)),
                            c.length > 8 ? v(c, 8) : "MONTH", intval(v(c, 9), 1), bool(v(c, 10))));
                    success++;
                } catch (Exception e) { errors.add(err(lineNo, e.getMessage())); }
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("total", total); out.put("success", success); out.put("failed", errors.size()); out.put("errors", errors);
            return out;
        } catch (Exception e) { throw BizException.param("CSV 读取失败：" + e.getMessage()); }
    }

    private static BigDecimal decimal(String s) { return s == null || s.isBlank() ? BigDecimal.ZERO : new BigDecimal(s); }
    private static Integer intval(String s, int def) { return s == null || s.isBlank() ? def : Integer.valueOf(s); }
    private static Boolean bool(String s) { return s != null && (s.equals("1") || s.equalsIgnoreCase("true") || s.equals("是")); }
    private static Map<String, Object> err(int line, String message) { Map<String, Object> m = new LinkedHashMap<>(); m.put("line", line); m.put("message", message); return m; }
    private static String v(String[] c, int i) { return i < c.length ? c[i].trim() : null; }
    private static String[] split(String line) {
        List<String> out = new ArrayList<>(); StringBuilder sb = new StringBuilder(); boolean quote = false;
        for (int i = 0; i < line.length(); i++) { char ch = line.charAt(i); if (ch == '"') { quote = !quote; continue; } if (ch == ',' && !quote) { out.add(sb.toString()); sb.setLength(0); } else sb.append(ch); }
        out.add(sb.toString()); return out.toArray(new String[0]);
    }
}
