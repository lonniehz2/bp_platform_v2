import io
p=r'src\pages\Applications.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { can } from '../permissions'","import { can, canAction } from '../permissions'")
s=s.replace("v-if=\"can('application')\" class=\"primary\" :disabled=\"busy\" @click=\"create\"","v-if=\"canAction('application:create', 'application')\" class=\"primary\" :disabled=\"busy\" @click=\"create\"")
s=s.replace("v-if=\"a.applicationStatus === 'DRAFT'\" @click=\"submit(a.id)\"","v-if=\"canAction('application:submit', 'application') && a.applicationStatus === 'DRAFT'\" @click=\"submit(a.id)\"")
s=s.replace("v-if=\"a.applicationStatus === 'SUBMITTED'\" @click=\"approve(a.id)\"","v-if=\"canAction('application:approve', 'application') && a.applicationStatus === 'SUBMITTED'\" @click=\"approve(a.id)\"")
s=s.replace("v-if=\"a.applicationStatus === 'SUBMITTED'\" @click=\"reject(a.id)\"","v-if=\"canAction('application:reject', 'application') && a.applicationStatus === 'SUBMITTED'\" @click=\"reject(a.id)\"")
s=s.replace("v-if=\"a.applicationStatus === 'SUBMITTED'\" @click=\"returnForSupplement(a.id)\"","v-if=\"canAction('application:return', 'application') && a.applicationStatus === 'SUBMITTED'\" @click=\"returnForSupplement(a.id)\"")
s=s.replace("v-if=\"a.applicationStatus === 'RETURNED'\" @click=\"resubmit(a.id)\"","v-if=\"canAction('application:resubmit', 'application') && a.applicationStatus === 'RETURNED'\" @click=\"resubmit(a.id)\"")
s=s.replace("v-if=\"a.applicationStatus === 'APPROVED'\" @click=\"wait(a.id)\"","v-if=\"canAction('application:waitlist', 'application') && a.applicationStatus === 'APPROVED'\" @click=\"wait(a.id)\"")
s=s.replace("<button class=\"primary\" :disabled=\"busy\" @click=\"allocate\">配租</button>","<button v-if=\"canAction('allocation:create', 'application')\" class=\"primary\" :disabled=\"busy\" @click=\"allocate\">配租</button>")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Contracts.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("v-if=\"can('contract')\" class=\"primary\" :disabled=\"busy\" @click=\"create\"","v-if=\"canAction('contract:create', 'contract')\" class=\"primary\" :disabled=\"busy\" @click=\"create\"")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('app/contract actions')
