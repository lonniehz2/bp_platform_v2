import io
p=r'src\main\java\com\yundao\platform\service\RelationImportService.java'
content='''package com.yundao.platform.service;

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
public class RelationImportService {

    private final JdbcTemplate jdbc;
    private final PersonService personService;

    public RelationImportService(JdbcTemplate jdbc, PersonService personService) {
        this.jdbc = jdbc;
        this.personService = personService;
    }

    public Map<String, Object> importPersonAssets(MultipartFile file) {
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
                line = line.replace("\\ufeff", "");
                if (line.isBlank() || line.startsWith("#")) continue;
                if (lineNo == 1 && (line.contains("项目编码") || line.toLowerCase().contains("projectcode"))) continue;
                total++;
                String[] c = split(line);
                if (c.length < 5) { errors.add(err(lineNo, "列数不足，至少需要项目编码、人员编码、房屋编码、关系类型")); continue; }
                try {
                    String projectCode = v(c, 0); String personCode = v(c, 1); String houseCode = v(c, 2);
                    String relationType = v(c, 3);
                    Long projectId = projects.get(projectCode);
                    if (projectId == null) throw new IllegalArgumentException("项目编码不存在：" + projectCode);
                    Map<String, Object> person = jdbc.queryForMap("select id from bp_person where tenant_id=? and person_code=? and is_deleted=0", tenant, personCode);
                    Map<String, Object> house = jdbc.queryForMap("select id from bp_house where tenant_id=? and org_id=? and house_code=? and is_deleted=0", tenant, projectId, houseCode);
                    personService.createRelation(((Number) person.get("id")).longValue(),
                            new PersonService.RelationCmd(projectId, "HOUSE", ((Number) house.get("id")).longValue(),
                                    normalize(relationType), bool(c, 6), date(c, 4), date(c, 5)));
                    success++;
                } catch (Exception e) { errors.add(err(lineNo, e.getMessage())); }
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("total", total); out.put("success", success); out.put("failed", errors.size()); out.put("errors", errors);
            return out;
        } catch (Exception e) { throw BizException.param("CSV 读取失败：" + e.getMessage()); }
    }

    private static String normalize(String s) {
        if (s == null) return "TENANT";
        return switch (s.trim().toUpperCase()) {
            case "TENANT", "承租人" -> "TENANT";
            case "FAMILY", "家庭成员" -> "FAMILY";
            case "COHABITANT", "同住人" -> "COHABITANT";
            case "OWNER", "产权人" -> "OWNER";
            default -> s.trim().toUpperCase();
        };
    }
    private static Map<String, Object> err(int line, String message) { Map<String, Object> m = new LinkedHashMap<>(); m.put("line", line); m.put("message", message); return m; }
    private static String v(String[] c, int i) { return i < c.length ? c[i].trim() : null; }
    private static LocalDate date(String s) { return s == null || s.isBlank() ? null : LocalDate.parse(s); }
    private static Boolean bool(String[] c, int i) { String s = v(c, i); return s != null && (s.equals("1") || s.equalsIgnoreCase("true") || s.equals("是")); }
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
s=s.replace('import com.yundao.platform.service.SpaceImportService;','import com.yundao.platform.service.SpaceImportService;\nimport com.yundao.platform.service.RelationImportService;')
s=s.replace('''    private final SpaceImportService spaceService;''','''    private final SpaceImportService spaceService;
    private final RelationImportService relationService;''')
s=s.replace('''    public PersonImportController(PersonImportService service, SpaceImportService spaceService) {
        this.service = service;
        this.spaceService = spaceService;
    }''','''    public PersonImportController(PersonImportService service, SpaceImportService spaceService,
                                  RelationImportService relationService) {
        this.service = service;
        this.spaceService = spaceService;
        this.relationService = relationService;
    }''')
s=s.replace('''    @PostMapping("/spaces")''','''    @PostMapping("/person-assets")
    public R<Map<String, Object>> personAssets(@RequestParam("file") MultipartFile file) {
        return R.ok(relationService.importPersonAssets(file));
    }

    @PostMapping("/spaces")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('relation import backend')
