# -*- coding: utf-8 -*-
"""修正回归脚本：房源不足时自动新建一套空置房源，保证摇号与签约可验证。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_check_flows.py')
s = io.open(P, encoding='utf-8').read()

helper = '''
def ensure_vacant_house(tok, oid):
    """确保有至少一套验收可用的空置房源：没有就用楼层下的房间新建一套。"""
    houses = rows(call('/houses?pageNum=1&pageSize=200&orgId=%s' % oid, token=tok))
    free = [h['id'] for h in houses if h.get('houseStatus') == 'VACANT']
    if free:
        return free
    tree = d(call('/spaces/tree?orgId=%s' % oid, token=tok))
    flat = []

    def walk(nodes):
        for n in nodes or []:
            flat.append(n)
            walk(n.get('children'))
    walk(tree if isinstance(tree, list) else (tree or {}).get('rows'))
    room = next((x for x in flat if x.get('spaceType') == 'ROOM'), None)
    floor = next((x for x in flat if x.get('spaceType') == 'FLOOR'), None)
    if not room and floor:
        st, r = call('/spaces', 'POST',
                     {'orgId': oid, 'spaceCode': 'CHK-R-' + time.strftime('%H%M%S'),
                      'spaceName': '回归房间', 'spaceType': 'ROOM',
                      'parentId': floor['id'], 'area': 55}, tok)
        room = d((st, r))
    if not room:
        return []
    st, r = call('/houses', 'POST',
                 {'orgId': oid, 'spaceId': room['id'],
                  'houseCode': 'CHK-' + time.strftime('%H%M%S'),
                  'houseName': TAG + '回归房源', 'houseType': 'PUBLIC_RENTAL',
                  'useType': 'CIVIL', 'area': 55, 'rentStandard': 15,
                  'rentUnit': 'AREA_MONTH', 'houseStatus': 'VACANT'}, tok)
    return [d((st, r))['id']] if d((st, r)) else []

'''

if 'def ensure_vacant_house' not in s:
    s = s.replace('def main():', helper + 'def main():', 1)

# 批次加房源处改用 helper
old = '''        houses = rows(call('/houses?pageNum=1&pageSize=100&orgId=%s' % oid, token=tok))
        vacant = [h['id'] for h in houses if h.get('houseStatus') == 'VACANT'][:2]'''
new = '''        vacant = ensure_vacant_house(tok, oid)[:2]'''
if old in s:
    s = s.replace(old, new, 1)

# 快捷签约处也用 helper
old2 = '''    persons = rows(call('/persons?pageNum=1&pageSize=1&orgId=%s' % oid, token=tok))
    houses = rows(call('/houses?pageNum=1&pageSize=100&orgId=%s' % oid, token=tok))
    free = [h['id'] for h in houses if h.get('houseStatus') == 'VACANT']'''
new2 = '''    persons = rows(call('/persons?pageNum=1&pageSize=1&orgId=%s' % oid, token=tok))
    free = ensure_vacant_house(tok, oid)'''
if old2 in s:
    s = s.replace(old2, new2, 1)

# 抄表处需要 houses 变量
if 'meter_items and houses' in s:
    s = s.replace('    if meter_items and houses:', '    if meter_items and free:', 1)
    s = s.replace("        hid = houses[0]['id']", "        hid = free[0]", 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('回归脚本已修正')
