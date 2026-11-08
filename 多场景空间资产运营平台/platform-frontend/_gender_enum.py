import io
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("'ADMIN':'管理员','STAFF':'员工'","'ADMIN':'管理员','MALE':'男','FEMALE':'女','STAFF':'员工'")
s=s.replace("'ADMIN':'Admin','STAFF':'Staff'","'ADMIN':'Admin','MALE':'Male','FEMALE':'Female','STAFF':'Staff'")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('gender enum')
