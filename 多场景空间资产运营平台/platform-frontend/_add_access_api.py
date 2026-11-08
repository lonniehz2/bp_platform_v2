import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'accessRecords' not in s:
 s=s.replace('''  workOrders: (projectId) => request(`/guarantee/work-orders?projectId=${projectId}`),''','''  accessRecords: (projectId) => request(`/guarantee/access-records?projectId=${projectId}`),
  createAccessRecord: (body) => request('/guarantee/access-records', { method: 'POST', body: JSON.stringify(body) }),
  approveAccessRecord: (id, status) => request(`/guarantee/access-records/${id}/approve`, { method: 'POST', body: JSON.stringify({ status }) }),
  workOrders: (projectId) => request(`/guarantee/work-orders?projectId=${projectId}`),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('access api')
