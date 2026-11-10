import io
p=r'src\main\java\com\yundao\platform\service\GrantImportService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public Map<String, Object> importDeviceGrants(MultipartFile file) {
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
                if (c.length < 5) { errors.add(err(lineNo, "列数不足，至少需要项目编码、人员编码、设备编码、开始日期、结束日期")); continue; }
                try {
                    String projectCode = v(c, 0); String personCode = v(c, 1); String deviceCode = v(c, 2);
                    Long projectId = projects.get(projectCode);
                    if (projectId == null) throw new IllegalArgumentException("项目编码不存在：" + projectCode);
                    Map<String, Object> person = jdbc.queryForMap("select id from bp_person where tenant_id=? and person_code=? and is_deleted=0", tenant, personCode);
                    Map<String, Object> device = jdbc.queryForMap("select id from bp_dev_device where tenant_id=? and project_id=? and device_code=? and is_deleted=0", tenant, projectId, deviceCode);
                    LocalDate start = date(v(c, 3);
                    LocalDate end = date(v(c, 4));
                    if (start == null || end == null) throw new IllegalArgumentException("设备授权起止日期必填");
                    grantService.create(new GrantService.GrantCmd(projectId, ((Number) person.get("id")).longValue(),
                            "DEVICE", ((Number) device.get("id")).longValue(), c.length > 5 ? v(c, 5) : "OPEN",
                            start, end, "IMPORT", null));
                    success++;
                } catch (Exception e) { errors.add(err(lineNo, e.getMessage())); }
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("total", total); out.put("success", success); out.put("failed", errors.size()); out.put("errors", errors);
            return out;
        } catch (Exception e) { throw BizException.param("CSV 读取失败：" + e.getMessage()); }
    }

'''
# fix typo line manually later
insert=insert.replace('LocalDate start = date(v(c, 3);','LocalDate start = date(v(c, 3));')
marker='''    private static Map<String, Object> err('''
if marker not in s: raise SystemExit('marker')
s=s.replace(marker,insert+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\PersonImportController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping("/grants")''','''    @PostMapping("/device-grants")
    public R<Map<String, Object>> deviceGrants(@RequestParam("file") MultipartFile file) {
        return R.ok(grantImportService.importDeviceGrants(file));
    }

    @PostMapping("/grants")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('device grant backend')
