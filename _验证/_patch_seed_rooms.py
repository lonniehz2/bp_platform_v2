# -*- coding: utf-8 -*-
"""修正造数脚本：房源必须挂在 ROOM 节点，先建 6 个房间再建房源。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_seed_phase1.py')
s = io.open(P, encoding='utf-8').read()

start = s.find('    if len(houses) < 6:')
end = s.find("    print('房源：%d 套' % len(houses))")
if start < 0 or end < 0:
    raise SystemExit('未找到房源段落')

new_block = '''    if len(houses) < 6:
        for i in range(1, 7):
            # 房间节点（房源必须挂 ROOM）
            room = next((x for x in spaces if x.get('spaceCode') == 'P1-R%d' % i), None)
            if not room:
                st, r = call('/spaces', 'POST',
                             {'orgId': org_id, 'spaceCode': 'P1-R%d' % i,
                              'spaceName': '1单元%03d室' % i, 'spaceType': 'ROOM',
                              'parentId': unit['id'], 'area': 60 + i, 'sortNo': i}, tok)
                room = d((st, r))
                if not room:
                    print('  房间 %d 失败：%s' % (i, msg((st, r))))
                    continue
            st, r = call('/houses', 'POST',
                         {'orgId': org_id, 'spaceId': room['id'],
                          'houseCode': 'P1-%03d' % i,
                          'houseName': '%s1号楼1单元%03d室' % (TAG, i),
                          'houseType': 'PUBLIC_RENTAL', 'useType': 'CIVIL',
                          'area': 60 + i, 'rentStandard': 15, 'rentUnit': 'AREA_MONTH',
                          'houseStatus': 'VACANT'}, tok)
            if (r or {}).get('code') != 'BP00000':
                print('  房源 %d 失败：%s' % (i, msg((st, r))))
        st, r = call('/houses?pageNum=1&pageSize=200&orgId=%s' % org_id, token=tok)
        houses = (d((st, r)) or {}).get('rows') or []

'''
s = s[:start] + new_block + s[end:]
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('房源段落已改为「先建 ROOM 再建房源」')
