import io
p=r'src\pages\Changes.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('<div class="panel-head"><h2>变更记录</h2><span class="small muted">{{ changes.length }} 条</span></div>','<div class="panel-head"><h2>变更记录</h2><span class="small muted">{{ changes.length }} 条 · 多级审批需逐级通过</span></div>')
s=s.replace('''<button class="sm" v-if="c.changeStatus === 'APPROVING'" @click="approve(c.id)">通过</button>''','''<button class="sm" v-if="c.changeStatus === 'APPROVING'" @click="approve(c.id)">通过当前节点</button>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("'合同数':'Contracts'","'合同数':'Contracts','通过当前节点':'Approve Current Step','多级审批需逐级通过':'Multi-level approval requires each step'")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('changes hint')
