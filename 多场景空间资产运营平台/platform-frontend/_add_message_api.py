import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'messages:' not in s:
 s=s.replace('''  openApps: () =>''','''  messages: () => request('/messages'),
  createMessage: (body) => request('/messages', { method: 'POST', body: JSON.stringify(body) }),
  readMessage: (id) => request(`/messages/${id}/read`, { method: 'POST' }),
  readAllMessages: () => request('/messages/read-all', { method: 'POST' }),
  openApps: () =>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('message api')
