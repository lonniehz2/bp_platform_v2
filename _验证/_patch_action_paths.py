# -*- coding: utf-8 -*-
import io
import os
import re

V = r'..\frontend\src\views'
files = ['Alerts.vue', 'Appeals.vue', 'Complaints.vue', 'Credits.vue', 'Keyring.vue']
for fn in files:
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    # 只替换模板里传给动作函数的路径，保留上传/下载的绝对地址
    s2 = s.replace(", '/api/v1/", ", '/")
    if s2 != s:
        io.open(p, 'w', encoding='utf-8', newline='').write(s2)
        print('paths fixed', fn)

# 处理人改为当前登录用户，去掉硬编码 1
for fn in ['Alerts.vue', 'Complaints.vue']:
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    if 'useAuthStore' not in s:
        s = s.replace("import req from '@/api/request'",
                      "import req from '@/api/request'\nimport { useAuthStore } from '@/store/auth'", 1)
        # 在 setup 内声明 auth（放在第一个 const 前）
        s = s.replace("</script>", "")
        # 找 script setup 开头
        m = re.search(r"<script setup>\n", s)
        if m:
            insert = m.end()
            s = s[:insert] + "const auth = useAuthStore()\n" + s[insert:]
        s += "</script>\n" if not s.rstrip().endswith('</script>') else ''
    s = s.replace('{ handleUserId: 1, action: label, result: value }',
                  '{ handleUserId: auth.user?.userId, action: label, result: value }')
    s = s.replace("handleUserId: 1, action: '处理'",
                  "handleUserId: auth.user?.userId, action: '处理'")
    s = s.replace("{ handleUserId: 1, action: '转工单' }",
                  "{ handleUserId: auth.user?.userId, action: '转工单' }")
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('handler user fixed', fn)
