import io
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("    if (currentLocale !== 'en-US') return\n    for (const m of mutations) {","    for (const m of mutations) {")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('observer fix')
