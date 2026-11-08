import io
p=r'src\pages\Billing.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { can } from '../permissions'","import { can, canAction } from '../permissions'")
s=s.replace("v-if=\"can('billing')\" class=\"primary\" :disabled=\"busy\" @click=\"pay\"","v-if=\"canAction('billing:pay', 'billing')\" class=\"primary\" :disabled=\"busy\" @click=\"pay\"")
s=s.replace("v-if=\"can('billing') && b.billStatus !== 'PAID'\" class=\"sm\" @click=\"openAdjust(b)\"","v-if=\"canAction('billing:adjust', 'billing') && b.billStatus !== 'PAID'\" class=\"sm\" @click=\"openAdjust(b)\"")
s=s.replace("v-if=\"can('billing')\" class=\"sm\" @click=\"openRefund(p)\"","v-if=\"canAction('billing:refund', 'billing')\" class=\"sm\" @click=\"openRefund(p)\"")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Contracts.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { can } from '../permissions'","import { can, canAction } from '../permissions'")
s=s.replace("v-if=\"can('billing') && c.contractStatus === 'ACTIVE'\" class=\"sm primary\" @click=\"openPayment(c)\"","v-if=\"canAction('billing:pay', 'billing') && c.contractStatus === 'ACTIVE'\" class=\"sm primary\" @click=\"openPayment(c)\"")
s=s.replace("v-if=\"can('contract') && c.contractStatus === 'DRAFT'\" class=\"sm\" :disabled=\"busy\" @click=\"contractAction(c, 'submit')\"","v-if=\"canAction('contract:submit', 'contract') && c.contractStatus === 'DRAFT'\" class=\"sm\" :disabled=\"busy\" @click=\"contractAction(c, 'submit')\"")
s=s.replace("v-if=\"can('contract') && c.contractStatus === 'DRAFT'\" class=\"sm\" :disabled=\"busy\" @click=\"contractAction(c, 'activate')\"","v-if=\"canAction('contract:activate', 'contract') && c.contractStatus === 'DRAFT'\" class=\"sm\" :disabled=\"busy\" @click=\"contractAction(c, 'activate')\"")
s=s.replace("v-if=\"can('contract') && c.contractStatus === 'DRAFT'\" class=\"sm danger\" :disabled=\"busy\" @click=\"contractAction(c, 'discard')\"","v-if=\"canAction('contract:discard', 'contract') && c.contractStatus === 'DRAFT'\" class=\"sm danger\" :disabled=\"busy\" @click=\"contractAction(c, 'discard')\"")
s=s.replace("v-if=\"can('contract') && c.contractStatus === 'APPROVING'\" class=\"sm primary\" :disabled=\"busy\" @click=\"contractAction(c, 'approve')\"","v-if=\"canAction('contract:approve', 'contract') && c.contractStatus === 'APPROVING'\" class=\"sm primary\" :disabled=\"busy\" @click=\"contractAction(c, 'approve')\"")
s=s.replace("v-if=\"can('contract') && c.contractStatus === 'APPROVING'\" class=\"sm\" :disabled=\"busy\" @click=\"contractAction(c, 'withdraw')\"","v-if=\"canAction('contract:withdraw', 'contract') && c.contractStatus === 'APPROVING'\" class=\"sm\" :disabled=\"busy\" @click=\"contractAction(c, 'withdraw')\"")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('button permissions')
