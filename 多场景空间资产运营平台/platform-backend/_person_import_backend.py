import io
p=r'src\main\java\com\yundao\platform\service\PersonImportService.java'
content='''package com.yundao.platform.service;

import com.yundao.platform.common.exception.BizException;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class PersonImportService {

    private final PersonService personService;

    public PersonImportService(PersonService personService) {
        this.personService = personService;
    }

    public Map<String, Object> importCsv(MultipartFile file) {
        if (file == null || file.isEmpty()) throw BizException.param("请上传 CSV 文件");
        List<Map<String, Object>> errors = new ArrayList<>();
        int total = 0, success = 0;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(file.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            int lineNo = 0;
            while ((line = reader.readLine()) != null) {
                lineNo++;
                line = line.replace("\\ufeff", "");
                if (line.isBlank() || line.startsWith("#")) continue;
                if (lineNo == 1 && (line.contains("人员编码") || line.toLowerCase().contains("personcode"))) continue;
                total++;
                String[] c = split(line);
                if (c.length < 2) {
                    errors.add(err(lineNo, "列数不足，至少需要人员编码、姓名"));
                    continue;
                }
                try {
                    personService.create(new PersonService.PersonCmd(
                            v(c, 0), v(c, 1), v(c, 2), v(c, 3), v(c, 4), v(c, 5),
                            date(v(c, 6)), v(c, 7), v(c, 8), v(c, 9), v(c, 10)));
                    success++;
                } catch (Exception e) {
                    errors.add(err(lineNo, e.getMessage()));
                }
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("total", total);
            out.put("success", success);
            out.put("failed", errors.size());
            out.put("errors", errors);
            return out;
        } catch (Exception e) {
            throw BizException.param("CSV 读取失败：" + e.getMessage());
        }
    }

    private static Map<String, Object> err(int line, String message) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("line", line);
        m.put("message", message);
        return m;
    }

    private static String v(String[] c, int i) {
        return i < c.length ? c[i].trim() : null;
    }

    private static LocalDate date(String s) {
        if (s == null || s.isBlank()) return null;
        try { return LocalDate.parse(s); } catch (Exception e) { throw new IllegalArgumentException("日期格式应为 yyyy-MM-dd：" + s); }
    }

    private static String[] split(String line) {
        List<String> out = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean quote = false;
        for (int i = 0; i < line.length(); i++) {
            char ch = line.charAt(i);
            if (ch == '"') { quote = !quote; continue; }
            if (ch == ',' && !quote) { out.add(sb.toString()); sb.setLength(0); }
            else sb.append(ch);
        }
        out.add(sb.toString());
        return out.toArray(new String[0]);
    }
}
'''
io.open(p,'w',encoding='utf-8',newline='').write(content)
p=r'src\main\java\com\yundao\platform\controller\PersonImportController.java'
content='''package com.yundao.platform.controller;

import com.yundao.platform.common.api.R;
import com.yundao.platform.service.PersonImportService;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/platform/imports")
public class PersonImportController {

    private final PersonImportService service;

    public PersonImportController(PersonImportService service) {
        this.service = service;
    }

    @PostMapping("/persons")
    public R<Map<String, Object>> persons(@RequestParam("file") MultipartFile file) {
        return R.ok(service.importCsv(file));
    }
}
'''
io.open(p,'w',encoding='utf-8',newline='').write(content)
print('person import backend')
