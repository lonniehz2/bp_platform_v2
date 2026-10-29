# -*- coding: utf-8 -*-
"""顶部改为「平台名 · 组织」，悬停显示平台编码与组织。"""
import io

files = [r'..\frontend\src\layout\LayoutRail.vue',
         r'..\frontend\src\layout\LayoutClassic.vue']
for f in files:
    s = io.open(f, encoding='utf-8').read()
    old_rail = '''        <el-tooltip placement="bottom"
                    :content="'平台：' + (auth.user?.tenantName || '—') + '（' + (auth.user?.tenantId || '—') + '）'">
          <el-tag size="small" type="info">
            组织 {{ auth.user?.orgName || '平台' }}
          </el-tag>
        </el-tooltip>'''
    new_rail = '''        <el-tooltip placement="bottom"
                    :content="'平台编码：' + (auth.user?.tenantId || '—') + ' ｜ 组织：' + (auth.user?.orgName || '平台')">
          <el-tag size="small" type="info">
            {{ auth.user?.tenantName || '平台' }} · {{ auth.user?.orgName || '平台' }}
          </el-tag>
        </el-tooltip>'''
    old_classic = '''        <el-tooltip placement="bottom"
                    :content="'平台：' + (auth.user?.tenantName || '—') + '（' + (auth.user?.tenantId || '—') + '）'">
          <el-tag size="small" type="info" style="margin-right:6px">
            组织 {{ auth.user?.orgName || '平台' }}
          </el-tag>
        </el-tooltip>'''
    new_classic = '''        <el-tooltip placement="bottom"
                    :content="'平台编码：' + (auth.user?.tenantId || '—') + ' ｜ 组织：' + (auth.user?.orgName || '平台')">
          <el-tag size="small" type="info" style="margin-right:6px">
            {{ auth.user?.tenantName || '平台' }} · {{ auth.user?.orgName || '平台' }}
          </el-tag>
        </el-tooltip>'''
    if old_classic in s:
        s = s.replace(old_classic, new_classic, 1)
    elif old_rail in s:
        s = s.replace(old_rail, new_rail, 1)
    io.open(f, 'w', encoding='utf-8', newline='').write(s)
print('headers updated')
