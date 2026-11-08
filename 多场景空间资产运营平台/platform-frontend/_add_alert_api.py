import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'alerts:' not in s:
 s=s.replace('''  publicities: (projectId) =>''','''  alerts: (projectId) => request(`/guarantee/alerts?projectId=${projectId}`),
  createAlert: (body) => request('/guarantee/alerts', { method: 'POST', body: JSON.stringify(body) }),
  handleAlert: (id, body) => request(`/guarantee/alerts/${id}/handle`, { method: 'POST', body: JSON.stringify(body) }),
  publicities: (projectId) =>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('alert api')
