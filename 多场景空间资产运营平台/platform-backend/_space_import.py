import io
p=r'src\main\java\com\yundao\platform\service\SpaceImportService.java'
content='''package com.yundao.platform.service;

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
public class SpaceImportService {

    private final JdbcTemplate jdbc;
    private final SpaceService spaceService;

    public SpaceImportService(JdbcTemplate jdbc, SpaceService spaceService) {
        this.jdbc = jdbc;
        this.spaceService = spaceService;
    }

    public Map<String, Object> importCsv(MultipartFile file) {
        if (file == null || file.isEmpty()) throw BizException.param("请上传 CSV 文件");
        String tenant = TenantContext.require();
        Map<String, Long> projectByCode = new HashMap<>();
        for (Map<String, Object> row : jdbc.queryForList(
                "select id, org_code orgCode from bp_org where tenant_id=? and is_deleted=0", tenant)) {
            projectByCode.put(String.valueOf(row.get("orgCode")), ((Number) row.get("id")).longValue());
        }
        List<Map<String, Object>> errors = new ArrayList<>();
        int total = 0, success = 0;
        Map<String, Long> spaceByKey = new HashMap<>();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {
            String line; int lineNo = 0;
            while ((line = reader.readLine()) != null) {
                lineNo++;
                line = line.replace("\\ufeff", "");
                if (line.isBlank() || line.startsWith("#")) continue;
                if (lineNo == 1 && (line.contains("项目编码") || line.toLowerCase().contains("projectcode"))) continue;
                total++;
                String[] c = split(line);
                if (c.length < 5) { errors.add(err(lineNo, "列数不足，至少需要项目编码、上级编码、空间编码、名称、类型")); continue; }
                try {
                    String projectCode = v(c, 0); String parentCode = v(c, 1);
                    String spaceCode = v(c, 2); String spaceName = v(c, 3); String spaceType = v(c, 4);
                    Long projectId = projectByCode.get(projectCode);
                    if (projectId == null) throw new IllegalArgumentException("项目编码不存在：" + projectCode);
                    Long parentId = null;
                    if (parentCode != null && !parentCode.isBlank()) {
                        parentId = spaceByKey.get(projectCode + ":" + parentCode);
                        if (parentId == null) throw new IllegalArgumentException("上级空间不存在或尚未导入：" + parentCode);
                    }
                    SpaceService.SpaceCmd cmd = new SpaceService.SpaceCmd(
                            parentId, spaceCode, spaceName, spaceType, v(c, 5), null,
                            num(c, 6), num(c, 7), bool(c, 8), null);
                    Map<String, Object> result = spaceService.create(projectId, cmd);
                    spaceByKey.put(projectCode + ":" + spaceCode, ((Number) result.get("id")).longValue());
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
    private static Double num(String[] c, int i) { String s = v(c, i); return s == null || s.isBlank() ? null : Double.valueOf(s); }
    private static Boolean bool(String[] c, int i) { String s = v(c, i); return s != null && (s.equals("1") || s.equalsIgnoreCase("true") || s.equals("是") || s.equalsIgnoreCase("Y")); }
    private static String[] split(String line) {
        List<String> out = new ArrayList<>(); StringBuilder sb = new StringBuilder(); boolean quote = false;
        for (int i = 0; i < line.length(); i++) { char ch = line.charAt(i); if (ch == '"') { quote = !quote; continue; } if (ch == ',' && !quote) { out.add(sb.toString()); sb.setLength(0); } else sb.append(ch); }
        out.add(sb.toString()); return out.toArray(new String[0]);
    }
}
'''
io.open(p,'w',encoding='utf-8',newline='').write(content)
p=r'src\main\java\com\yundao\platform\controller\PersonImportController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace("    private final PersonImportService service;\n\n    public PersonImportController(PersonImportService service) {\n        this.service = service;\n    }","    private final PersonImportService service;\n    private final SpaceImportService spaceService;\n\n    public PersonImportController(PersonImportService service, SpaceImportService spaceService) {\n        this.service = service;\n        this.spaceService = spaceService;\n    }")
s=s.replace('''    @PostMapping("/persons")
    public R<Map<String, Object>> persons(@RequestParam("file") MultipartFile file) {
        return R.ok(service.importCsv(file));
    }''','''    @PostMapping("/persons")
    public R<Map<String, Object>> persons(@RequestParam("file") MultipartFile file) {
        return R.ok(service.importCsv(file));
    }

    @PostMapping("/spaces")
    public R<Map<String, Object>> spaces(@RequestParam("file") MultipartFile file) {
        return R.ok(spaceService.importCsv(file));
    }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('space import backend')
