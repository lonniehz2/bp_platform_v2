package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import com.yundao.platform.common.tenant.TenantContext;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class UserImportService {

    private final JdbcTemplate jdbc;
    private final UserService userService;

    public UserImportService(JdbcTemplate jdbc, UserService userService) {
        this.jdbc = jdbc;
        this.userService = userService;
    }

    public Map<String, Object> importCsv(MultipartFile file) {
        if (file == null || file.isEmpty()) throw BizException.param("请上传 CSV 文件");
        String tenant = TenantContext.require();
        Map<String, Long> roles = new HashMap<>();
        for (Map<String, Object> row : jdbc.queryForList(
                "select id, role_code roleCode from bp_role where tenant_id=? and scene_code='GUARANTEE' and is_deleted=0", tenant)) {
            roles.put(String.valueOf(row.get("roleCode")), ((Number) row.get("id")).longValue());
        }
        List<Map<String, Object>> errors = new ArrayList<>();
        int total = 0, success = 0;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {
            String line; int lineNo = 0;
            while ((line = reader.readLine()) != null) {
                lineNo++;
                line = line.replace("\ufeff", "");
                if (line.isBlank() || line.startsWith("#")) continue;
                if (lineNo == 1 && (line.contains("用户名") || line.toLowerCase().contains("username"))) continue;
                total++;
                String[] c = split(line);
                if (c.length < 3) { errors.add(err(lineNo, "列数不足，至少需要用户名、密码、姓名")); continue; }
                try {
                    List<Long> roleIds = new ArrayList<>();
                    if (c.length > 3 && c[3] != null && !c[3].isBlank()) {
                        for (String code : c[3].split("[|,，]")) {
                            Long roleId = roles.get(code.trim());
                            if (roleId == null) throw new IllegalArgumentException("角色编码不存在：" + code);
                            roleIds.add(roleId);
                        }
                    }
                    userService.create(new UserService.CreateCmd(c[0].trim(), c[1], c[2].trim(), roleIds));
                    success++;
                } catch (Exception e) { errors.add(err(lineNo, e.getMessage())); }
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("total", total); out.put("success", success); out.put("failed", errors.size()); out.put("errors", errors);
            return out;
        } catch (Exception e) { throw BizException.param("CSV 读取失败：" + e.getMessage()); }
    }

    private static Map<String, Object> err(int line, String message) { Map<String, Object> m = new LinkedHashMap<>(); m.put("line", line); m.put("message", message); return m; }
    private static String[] split(String line) {
        List<String> out = new ArrayList<>(); StringBuilder sb = new StringBuilder(); boolean quote = false;
        for (int i = 0; i < line.length(); i++) { char ch = line.charAt(i); if (ch == '"') { quote = !quote; continue; } if (ch == ',' && !quote) { out.add(sb.toString()); sb.setLength(0); } else sb.append(ch); }
        out.add(sb.toString()); return out.toArray(new String[0]);
    }
}
