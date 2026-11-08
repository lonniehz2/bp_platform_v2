import io
p=r'src\main\java\com\yundao\platform\service\PermissionService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''            case "AUDITOR" -> List.of("*:view");''','''            case "AUDITOR" -> List.of("*:view");
            case "GUARANTEE_FINANCE", "FINANCE" -> List.of("billing:*", "deposit:*", "subsidy:*", "contract:view");''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\service\DataScopeService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''        if (roles.contains("GUARANTEE_ADMIN") || roles.contains("ADMIN")) {
            return null;
        }''','''        if (roles.contains("GUARANTEE_ADMIN") || roles.contains("ADMIN") || roles.contains("AUDITOR")) {
            return null;
        }''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('finance/auditor mapping')
