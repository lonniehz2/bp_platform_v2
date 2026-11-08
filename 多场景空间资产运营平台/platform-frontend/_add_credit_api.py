import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'credits:' not in s:
 s=s.replace('''  alerts: (projectId) => request(`/guarantee/alerts?projectId=${projectId}`),''','''  credits: (projectId) => request(`/guarantee/credits?projectId=${projectId}`),
  createCredit: (body) => request('/guarantee/credits', { method: 'POST', body: JSON.stringify(body) }),
  revokeCredit: (id) => request(`/guarantee/credits/${id}/revoke`, { method: 'POST' }),
  alerts: (projectId) => request(`/guarantee/alerts?projectId=${projectId}`),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('credit api')
