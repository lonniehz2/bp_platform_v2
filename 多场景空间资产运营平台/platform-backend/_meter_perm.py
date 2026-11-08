import io
p=r'src\main\java\com\yundao\platform\config\PermissionInterceptor.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''        if (path.startsWith("/api/v1/platform/projects")''','''        if (path.startsWith("/api/v1/platform/guarantee/meters")) {
            return "asset";
        }
        if (path.startsWith("/api/v1/platform/projects")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('meter permission')
