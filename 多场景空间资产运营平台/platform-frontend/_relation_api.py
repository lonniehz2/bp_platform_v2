import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'relations:' not in s:
 s=s.replace("  createPerson: (body) => request('/persons', { method: 'POST', body: JSON.stringify(body) }),","  createPerson: (body) => request('/persons', { method: 'POST', body: JSON.stringify(body) }),\n  relations: (personId) => request(`/persons/${personId}/relations`),\n  createRelation: (personId, body) => request(`/persons/${personId}/relations`, { method: 'POST', body: JSON.stringify(body) }),")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('relation api')
