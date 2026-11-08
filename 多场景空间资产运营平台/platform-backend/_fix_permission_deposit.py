import io
p=r'src\main\java\com\yundao\platform\config\PermissionInterceptor.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''        if (path.startsWith("/api/v1/platform/guarantee/contracts")''','''        if (path.contains("/deposit") || path.contains("/subsidies")) {
            return "billing";
        }
        if (path.startsWith("/api/v1/platform/guarantee/contracts")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('deposit mapping fixed')
