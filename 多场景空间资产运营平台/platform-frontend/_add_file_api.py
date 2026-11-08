import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  if (options.body && !headers['Content-Type']) {","  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {")
if 'uploadFile' not in s:
 s=s.replace("  users: () => request('/users'),","  files: (bizType, bizId) => request(`/files?bizType=${bizType}&bizId=${bizId}`),\n  uploadFile: (bizType, bizId, file) => { const fd = new FormData(); fd.append('file', file); return request(`/files?bizType=${bizType}&bizId=${bizId}`, { method: 'POST', body: fd }) },\n  downloadFile: async (id, name) => { const res = await fetch(`${BASE}/files/${id}/download`, { headers: { Authorization: `Bearer ${token()}` } }); if (!res.ok) throw new Error('下载失败'); const blob = await res.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name || 'download'; a.click(); URL.revokeObjectURL(a.href) },\n  users: () => request('/users'),")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('file api')
