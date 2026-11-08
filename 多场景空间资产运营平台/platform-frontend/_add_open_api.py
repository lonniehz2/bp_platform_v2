import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'openApps' not in s:
 s=s.replace('''  shortRentOrders: (projectId) =>''','''  openApps: () => request('/open-apps'),
  createOpenApp: (body) => request('/open-apps', { method: 'POST', body: JSON.stringify(body) }),
  toggleOpenApp: (id, enabled) => request(`/open-apps/${id}/toggle?enabled=${enabled}`, { method: 'POST' }),
  shortRentOrders: (projectId) =>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('open api')
