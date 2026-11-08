import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''  generateBill: (contractId, body) => request(`/guarantee/contracts/${contractId}/bills`, { method: 'POST', body: JSON.stringify(body) }),''','''  generateBill: (contractId, body) => request(`/guarantee/contracts/${contractId}/bills`, { method: 'POST', body: JSON.stringify(body) }),
  deposit: (contractId) => request(`/guarantee/contracts/${contractId}/deposit`),
  payDeposit: (contractId, body) => request(`/guarantee/contracts/${contractId}/deposit/pay`, { method: 'POST', body: JSON.stringify(body) }),
  refundDeposit: (depositId, body) => request(`/guarantee/deposits/${depositId}/refund`, { method: 'POST', body: JSON.stringify(body) }),
  subsidies: (contractId) => request(`/guarantee/contracts/${contractId}/subsidies`),
  createSubsidy: (contractId, body) => request(`/guarantee/contracts/${contractId}/subsidies`, { method: 'POST', body: JSON.stringify(body) }),
  changes: (contractId) => request(`/guarantee/contracts/${contractId}/changes`),
  createChange: (contractId, body) => request(`/guarantee/contracts/${contractId}/changes`, { method: 'POST', body: JSON.stringify(body) }),
  submitChange: (changeId) => request(`/guarantee/contract-changes/${changeId}/submit`, { method: 'POST' }),
  approveChange: (changeId, body) => request(`/guarantee/contract-changes/${changeId}/approve`, { method: 'POST', body: JSON.stringify(body) }),
  rejectChange: (changeId, body) => request(`/guarantee/contract-changes/${changeId}/reject`, { method: 'POST', body: JSON.stringify(body) }),
  workflowTasks: (status = '') => request(`/workflow-tasks${status ? `?status=${status}` : ''}`),
  approveTask: (taskId, body) => request(`/workflow-tasks/${taskId}/approve`, { method: 'POST', body: JSON.stringify(body) }),
  rejectTask: (taskId, body) => request(`/workflow-tasks/${taskId}/reject`, { method: 'POST', body: JSON.stringify(body) }),
  workflowRecords: (taskId) => request(`/workflow-tasks/${taskId}/records`),''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('api extended')
