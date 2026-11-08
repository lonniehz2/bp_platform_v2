import io
p=r'src\pages\Changes.vue'
s=io.open(p,encoding='utf-8').read()
old='<td><span class="badge" :class="statusClass(c.changeStatus)">{{ c.changeStatus }}</span></td>'
new='''<td>
                  <span class="badge" :class="statusClass(c.changeStatus)">{{ c.changeStatus }}</span>
                  <div v-if="c.changeStatus === 'APPROVING' && c.currentNode" class="small muted">当前节点：{{ c.currentNode }}</div>
                </td>'''
if old not in s: raise SystemExit('status marker missing')
s=s.replace(old,new,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('node ui inserted')
