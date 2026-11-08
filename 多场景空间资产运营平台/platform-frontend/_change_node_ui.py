import io
p=r'src\pages\Changes.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''                  <td><span class="badge" :class="c.changeStatus === 'APPROVED' ? 'green' : c.changeStatus === 'REJECTED' ? 'red' : 'orange'">{{ c.changeStatus }}</span></td>''','''                  <td>
                    <span class="badge" :class="c.changeStatus === 'APPROVED' ? 'green' : c.changeStatus === 'REJECTED' ? 'red' : 'orange'">{{ c.changeStatus }}</span>
                    <div v-if="c.changeStatus === 'APPROVING' && c.currentNode" class="small muted">当前节点：{{ c.currentNode }}</div>
                  </td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("'合同数':'Contracts'","'合同数':'Contracts','当前节点：':'Current step: '")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('current node frontend')
