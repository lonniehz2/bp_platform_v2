package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.io.BufferedReader;
import java.io.InputStreamReader;
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
public class GrantImportService {

    private final JdbcTemplate jdbc;
    private final GrantService grantService;

    public GrantImportService(JdbcTemplate jdbc, GrantService grantService) {
        this.jdbc = jdbc;
        this.grantService = grantService;
    }

    public Map<String, Object> importSpaceGrants(MultipartFile file) {
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
                if (c.length < 3) { errors.add(err(lineNo, "列数不足，至少需要项目编码、人员编码、空间编码")); continue; }
                try {
                    String projectCode = v(c, 0); String personCode = v(c, 1); String spaceCode = v(c, 2);
                    Long projectId = projects.get(projectCode);
                    if (projectId == null) throw new IllegalArgumentException("项目编码不存在：" + projectCode);
                    Map<String, Object> person = jdbc.queryForMap("select id from bp_person where tenant_id=? and person_code=? and is_deleted=0", tenant, personCode);
                    Map<String, Object> space = jdbc.queryForMap("select id from bp_space where tenant_id=? and org_id=? and space_code=? and is_deleted=0", tenant, projectId, spaceCode);
                    grantService.create(new GrantService.GrantCmd(projectId, ((Number) person.get("id")).longValue(),
                            "SPACE", ((Number) space.get("id")).longValue(), c.length > 3 ? v(c, 3) : "OPEN",
                            date(v(c, 4)), date(v(c, 5)), "IMPORT", null));
                    success++;
                } catch (Exception e) { errors.add(err(lineNo, e.getMessage())); }
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("total", total); out.put("success", success); out.put("failed", errors.size()); out.put("errors", errors);
            return out;
        } catch (Exception e) { throw BizException.param("CSV 读取失败：" + e.getMessage()); }
    }

    private static Map<String, Object> err(int line, String message) { Map<String, Object> m = new LinkedHashMap<>(); m.put("line", line); m.put("message", message); return m; }
    private static String v(String[] c, int i) { return i < c.length ? c[i].trim() : null; }
    private static LocalDate date(String s) { return s == null || s.isBlank() ? null : LocalDate.parse(s); }
    private static String[] split(String line) {
        List<String> out = new ArrayList<>(); StringBuilder sb = new StringBuilder(); boolean quote = false;
        for (int i = 0; i < line.length(); i++) { char ch = line.charAt(i); if (ch == '"') { quote = !quote; continue; } if (ch == ',' && !quote) { out.add(sb.toString()); sb.setLength(0); } else sb.append(ch); }
        out.add(sb.toString()); return out.toArray(new String[0]);
    }
}
