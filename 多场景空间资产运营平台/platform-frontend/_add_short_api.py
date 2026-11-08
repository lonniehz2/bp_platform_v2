import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'shortRentOrders' not in s:
 s=s.replace('''  credits: (projectId) => request(`/guarantee/credits?projectId=${projectId}`),''','''  shortRentOrders: (projectId) => request(`/guarantee/short-rent-orders?projectId=${projectId}`),
  createShortRentOrder: (body) => request('/guarantee/short-rent-orders', { method: 'POST', body: JSON.stringify(body) }),
  updateShortRentStatus: (id, status) => request(`/guarantee/short-rent-orders/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  credits: (projectId) => request(`/guarantee/credits?projectId=${projectId}`),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('short api')
