# -*- coding: utf-8 -*-
"""放宽种子脚本的租户校验：主表为空时仅告警（本环境角色数据已存在）"""
import io

P = r'D:\Work\业务平台开发\_验证\_seed_open_gov.py'
s = io.open(P, encoding='utf-8').read()

old_start = s.find('if cur.fetchone()[0] == 0:')
if old_start == -1:
    print('未找到租户校验块')
else:
    # 找到该 if 块结束（下一处 conn.close()）
    end = s.find('sys.exit(3)', old_start)
    end = s.find('\n', end) + 1
    old_block = s[old_start:end]
    new_block = '''if cur.fetchone()[0] == 0:
    print('⚠️ 租户主表 bp_iam_tenant 无 %s 记录（本环境主表未用），'
          '继续写入权限/字典' % TENANT)
'''
    s = s[:old_start] + new_block + s[end:]
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已放宽租户校验（原块 %d 行 → 2 行）' % old_block.count('\n'))
