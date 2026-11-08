import io
p=r'src\main\resources\application.yml'
s=io.open(p,encoding='utf-8').read()
if 'multipart' not in s:
 s=s.replace('''  jackson:''','''  servlet:
    multipart:
      max-file-size: 20MB
      max-request-size: 25MB
  jackson:''')
if 'bp:' not in s:
 s += '''

bp:
  file:
    root: ${FILE_ROOT:uploads}
  auth:
    secret: ${AUTH_SECRET:dev-only-change-me}
    ttl-seconds: 28800
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('config updated')
