import io
p=r'platform-sql\001_platform_core.sql'
s=io.open(p,encoding='utf-8').read()
if 'contact_name varchar(64)' not in s:
 s=s.replace('''  default_asset_type_code varchar(64) null,
  org_path''','''  default_asset_type_code varchar(64) null,
  address varchar(255) null,
  contact_name varchar(64) null,
  contact_phone varchar(32) null,
  remark varchar(500) null,
  org_path''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('org schema')
