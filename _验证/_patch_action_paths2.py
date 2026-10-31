# -*- coding: utf-8 -*-
import io
import os

V = r'..\frontend\src\views'
for fn in ['Alerts.vue', 'Appeals.vue', 'Complaints.vue', 'Credits.vue', 'Keyring.vue']:
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    s2 = s.replace(", '/api/v1/", ", '/")
    if s2 != s:
        io.open(p, 'w', encoding='utf-8', newline='').write(s2)
        print('paths fixed', fn)

for fn in ['Alerts.vue', 'Complaints.vue']:
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    if 'useAuthStore' not in s:
        s = s.replace("import req from '@/api/request'",
                      "import req from '@/api/request'\nimport { useAuthStore } from '@/store/auth'", 1)
        lines = s.splitlines()
        last_import = max(i for i, l in enumerate(lines) if l.startswith('import '))
        lines.insert(last_import + 1, '\nconst auth = useAuthStore()')
        s = '\n'.join(lines)
    s = s.replace('{ handleUserId: 1, action: label, result: value }',
                  '{ handleUserId: auth.user?.userId, action: label, result: value }')
    s = s.replace("handleUserId: 1, action: '处理'",
                  "handleUserId: auth.user?.userId, action: '处理'")
    s = s.replace("{ handleUserId: 1, action: '转工单' }",
                  "{ handleUserId: auth.user?.userId, action: '转工单' }")
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('handler user fixed', fn)
