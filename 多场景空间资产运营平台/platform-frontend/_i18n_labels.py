import io
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      publicity: '公示管理',","      publicity: '公示管理',\n      publicities: '公示管理',\n      menus: '菜单与角色',",1)
s=s.replace("      publicity: 'Publicity',","      publicity: 'Publicity',\n      publicities: 'Publicity',\n      menus: 'Menus & Roles',",1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('i18n')
