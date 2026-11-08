import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'cohabitants' not in s:
 s=s.replace("  files: (bizType, bizId) => request(`/files?bizType=${bizType}&bizId=${bizId}`),","  cohabitants: (contractId) => request(`/guarantee/contracts/${contractId}/cohabitants`),\n  addCohabitant: (contractId, body) => request(`/guarantee/contracts/${contractId}/cohabitants`, { method: 'POST', body: JSON.stringify(body) }),\n  removeCohabitant: (id) => request(`/guarantee/contract-cohabitants/${id}/remove`, { method: 'POST' }),\n  files: (bizType, bizId) => request(`/files?bizType=${bizType}&bizId=${bizId}`),")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('cohabitant api')
