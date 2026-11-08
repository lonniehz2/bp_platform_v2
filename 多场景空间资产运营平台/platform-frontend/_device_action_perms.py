import io
p=r'src\pages\Devices.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { can } from '../permissions'","import { can, canAction } from '../permissions'")
s=s.replace("v-if=\"can('device')\" class=\"primary\" :disabled=\"busy\" @click=\"createDevice\"","v-if=\"canAction('device:create', 'device')\" class=\"primary\" :disabled=\"busy\" @click=\"createDevice\"")
s=s.replace("<button class=\"primary\" :disabled=\"busy\" @click=\"createGrant\">新增授权</button>","<button v-if=\"canAction('device:grant', 'device')\" class=\"primary\" :disabled=\"busy\" @click=\"createGrant\">新增授权</button>")
s=s.replace("v-if=\"g.grantStatus === 'ACTIVE'\" class=\"sm danger\" :disabled=\"busy\" @click=\"revokeGrant(g)\"","v-if=\"canAction('device:grant', 'device') && g.grantStatus === 'ACTIVE'\" class=\"sm danger\" :disabled=\"busy\" @click=\"revokeGrant(g)\"")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('device perms')
