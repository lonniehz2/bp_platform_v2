import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'workOrders' not in s:
 s=s.replace('''  meters: (projectId) => request(`/guarantee/meters?projectId=${projectId}`),''','''  workOrders: (projectId) => request(`/guarantee/work-orders?projectId=${projectId}`),
  createWorkOrder: (body) => request('/guarantee/work-orders', { method: 'POST', body: JSON.stringify(body) }),
  updateWorkOrder: (id, body) => request(`/guarantee/work-orders/${id}/update`, { method: 'POST', body: JSON.stringify(body) }),
  meters: (projectId) => request(`/guarantee/meters?projectId=${projectId}`),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('workorder api')
