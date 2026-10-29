# -*- coding: utf-8 -*-
import io

# 1) Help 文案
p = r'..\frontend\src\help.js'
s = io.open(p, encoding='utf-8').read()
s = s.replace("'输入租户ID（默认 350600）、用户名、密码，点击「登录」。'",
              "'输入平台租户码（默认 350600；它是数据隔离标识，不是组织编码）、用户名、密码，点击「登录」。'", 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)

# 2) H5 登录占位
p = r'..\frontend\src\views\H5Login.vue'
s = io.open(p, encoding='utf-8').read()
s = s.replace('placeholder="租户ID"', 'placeholder="平台租户码"', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)

# 3) LayoutClassic 增加组织标签
p = r'..\frontend\src\layout\LayoutClassic.vue'
s = io.open(p, encoding='utf-8').read()
if 'orgName' not in s:
    s = s.replace('''        <el-tag size="small" type="info">{{ auth.displayName || '管理员' }}</el-tag>''',
                  '''        <el-tooltip placement="bottom"
                    :content="'租户：' + (auth.user?.tenantName || '—') + '（' + (auth.user?.tenantId || '—') + '）'">
          <el-tag size="small" type="info" style="margin-right:6px">
            组织 {{ auth.user?.orgName || '平台' }}
          </el-tag>
        </el-tooltip>
        <el-tag size="small" type="info">{{ auth.displayName || '管理员' }}</el-tag>''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('help/h5/classic updated')
