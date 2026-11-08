import io
p=r'src\main\java\com\yundao\platform\service\GuaranteeContractService.java'
s=io.open(p,encoding='utf-8').read().replace('''                cmd.billingCycle(), cmd.billDay()));''','''                cmd.billingCycle(), cmd.billDay(), false));''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('constructor fixed')
