import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'users:' not in s:
 s=s.replace('''  messages: () => request('/messages'),''','''  users: () => request('/users'),
  userRoles: () => request('/users/roles'),
  createUser: (body) => request('/users', { method: 'POST', body: JSON.stringify(body) }),
  updateUser: (id, body) => request(`/users/${id}/update`, { method: 'POST', body: JSON.stringify(body) }),
  messages: () => request('/messages'),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('user api')
