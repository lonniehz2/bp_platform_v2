import io
p=r'src\main\java\com\yundao\platform\service\ProjectService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''                            + "values(?,?,?,?,?,'PROJECT',?,?,?,?,?,?,?,?,0,'ENABLED',0)",''','''                            + "values(?,?,?,?,?,'PROJECT',?,?,?,?,?,?,?,?,?,0,'ENABLED',0)",''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('placeholder fix')
