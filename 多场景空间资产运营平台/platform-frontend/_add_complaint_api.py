import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'complaints' not in s:
 s=s.replace('''  accessRecords: (projectId) => request(`/guarantee/access-records?projectId=${projectId}`),''','''  complaints: (projectId, type) => request(`/guarantee/complaints?projectId=${projectId}${type ? '&type=' + type : ''}`),
  createComplaint: (body) => request('/guarantee/complaints', { method: 'POST', body: JSON.stringify(body) }),
  handleComplaint: (id, body) => request(`/guarantee/complaints/${id}/handle`, { method: 'POST', body: JSON.stringify(body) }),
  accessRecords: (projectId) => request(`/guarantee/access-records?projectId=${projectId}`),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('complaint api')
