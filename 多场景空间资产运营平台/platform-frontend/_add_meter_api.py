import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'meters:' not in s:
 s=s.replace('''  devices: (projectId) => request(`/devices?projectId=${projectId}`),''','''  meters: (projectId) => request(`/guarantee/meters?projectId=${projectId}`),
  createMeter: (body) => request('/guarantee/meters', { method: 'POST', body: JSON.stringify(body) }),
  meterReadings: (meterId) => request(`/guarantee/meters/${meterId}/readings`),
  readMeter: (meterId, body) => request(`/guarantee/meters/${meterId}/readings`, { method: 'POST', body: JSON.stringify(body) }),
  meterSummary: (projectId) => request(`/guarantee/meters/summary?projectId=${projectId}`),
  devices: (projectId) => request(`/devices?projectId=${projectId}`),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('meter api')
