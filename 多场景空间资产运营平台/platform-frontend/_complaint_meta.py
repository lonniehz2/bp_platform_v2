import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("{ path: '/visits', component: Complaints, meta: { title: '入户走访' } }","{ path: '/visits', component: Complaints, meta: { title: '入户走访', complaintType: 'VISIT' } }")
s=s.replace("{ path: '/appeals', component: Complaints, meta: { title: '申诉管理' } }","{ path: '/appeals', component: Complaints, meta: { title: '申诉管理', complaintType: 'APPEAL' } }")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('meta')
