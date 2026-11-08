import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'bindDevice' not in s:
 s=s.replace("  createDevice: (body) => request('/devices', { method: 'POST', body: JSON.stringify(body) }),","  createDevice: (body) => request('/devices', { method: 'POST', body: JSON.stringify(body) }),\n  bindDevice: (id, spaceId) => request(`/devices/${id}/bind`, { method: 'POST', body: JSON.stringify({ spaceId }) }),")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('bind api')
