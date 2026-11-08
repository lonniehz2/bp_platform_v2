import io
p=r'src\main\java\com\yundao\platform\service\BillingService.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''                        + "where b.tenant_id=? and b.project_id=? and b.is_deleted=0 "
                        + "and (? is null or b.bill_status=?) order by b.id desc",''','''                        + "where b.tenant_id=? and b.project_id=? and b.is_deleted=0 "
                        + "and (? is null or b.bill_status=?) order by b.create_time desc, b.id desc",''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('order')
