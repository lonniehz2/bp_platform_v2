import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'rejectApplication' not in s:
 s=s.replace("  submitApplication: (id) => request(`/guarantee/applications/${id}/submit`, { method: 'POST' }),","  submitApplication: (id) => request(`/guarantee/applications/${id}/submit`, { method: 'POST' }),\n  rejectApplication: (id, comment) => request(`/guarantee/applications/${id}/reject`, { method: 'POST', body: JSON.stringify({ comment }) }),\n  returnApplication: (id, comment) => request(`/guarantee/applications/${id}/return`, { method: 'POST', body: JSON.stringify({ comment }) }),\n  resubmitApplication: (id) => request(`/guarantee/applications/${id}/resubmit`, { method: 'POST' }),")
if 'submitContract' not in s:
 s=s.replace("  createContract: (body) => request('/guarantee/contracts', { method: 'POST', body: JSON.stringify(body) }),","  createContract: (body) => request('/guarantee/contracts', { method: 'POST', body: JSON.stringify(body) }),\n  submitContract: (id) => request(`/guarantee/contracts/${id}/submit`, { method: 'POST' }),\n  approveContract: (id) => request(`/guarantee/contracts/${id}/approve`, { method: 'POST' }),\n  activateContract: (id, reason) => request(`/guarantee/contracts/${id}/activate`, { method: 'POST', body: JSON.stringify({ reason }) }),\n  withdrawContract: (id) => request(`/guarantee/contracts/${id}/withdraw`, { method: 'POST' }),\n  discardContract: (id) => request(`/guarantee/contracts/${id}/discard`, { method: 'POST' }),")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Applications.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("async function wait(id) { await run(() => api.joinWaitlist(id)) }","async function wait(id) { await run(() => api.joinWaitlist(id)) }\nasync function reject(id) { const comment = window.prompt('驳回原因') || '资料不齐'; await run(() => api.rejectApplication(id, comment)) }\nasync function returnForSupplement(id) { const comment = window.prompt('退回补充原因') || '请补充资料'; await run(() => api.returnApplication(id, comment)) }\nasync function resubmit(id) { await run(() => api.resubmitApplication(id)) }")
s=s.replace('''                  <button class="sm" v-if="a.applicationStatus === 'SUBMITTED'" @click="approve(a.id)">审核通过</button>
                  <button class="sm" v-if="a.applicationStatus === 'APPROVED'" @click="wait(a.id)">进入轮候</button>''','''                  <button class="sm" v-if="a.applicationStatus === 'SUBMITTED'" @click="approve(a.id)">审核通过</button>
                  <button class="sm danger" v-if="a.applicationStatus === 'SUBMITTED'" @click="reject(a.id)">驳回</button>
                  <button class="sm" v-if="a.applicationStatus === 'SUBMITTED'" @click="returnForSupplement(a.id)">退回补充</button>
                  <button class="sm" v-if="a.applicationStatus === 'RETURNED'" @click="resubmit(a.id)">重新提交</button>
                  <button class="sm" v-if="a.applicationStatus === 'APPROVED'" @click="wait(a.id)">进入轮候</button>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('app ui actions')
