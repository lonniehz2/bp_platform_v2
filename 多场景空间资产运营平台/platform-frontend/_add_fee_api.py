import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'feeItems' not in s:
 s=s.replace('''  bills: (projectId) => request(`/bills?projectId=${projectId}`),''','''  feeItems: (projectId) => request(`/guarantee/fee-items?projectId=${projectId}`),
  createFeeItem: (body) => request('/guarantee/fee-items', { method: 'POST', body: JSON.stringify(body) }),
  toggleFeeItem: (id, enabled) => request(`/guarantee/fee-items/${id}/toggle?enabled=${enabled}`, { method: 'POST' }),
  bills: (projectId) => request(`/bills?projectId=${projectId}`),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('fee api')
