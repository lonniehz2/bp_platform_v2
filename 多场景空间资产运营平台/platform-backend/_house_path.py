import io
p=r'src\main\java\com\yundao\platform\controller\HouseController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    public R<Map<String, Object>> update(@org.springframework.web.bind.annotation.PathVariable long houseId,''','''    public R<Map<String, Object>> update(@org.springframework.web.bind.annotation.PathVariable long projectId,
                                         @org.springframework.web.bind.annotation.PathVariable long houseId,''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'platform-frontend\src\api.js'.replace('platform-backend\\','')
