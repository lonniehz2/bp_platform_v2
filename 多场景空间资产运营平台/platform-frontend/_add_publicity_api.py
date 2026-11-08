import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'publicities' not in s:
 s=s.replace('''  complaints: (projectId, type) =>''','''  publicities: (projectId) => request(`/guarantee/publicities?projectId=${projectId}`),
  createPublicity: (body) => request('/guarantee/publicities', { method: 'POST', body: JSON.stringify(body) }),
  updatePublicityStatus: (id, status) => request(`/guarantee/publicities/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  complaints: (projectId, type) =>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('publicity api')
