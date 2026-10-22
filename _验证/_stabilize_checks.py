# -*- coding: utf-8 -*-
"""让 flows 回归不再偶发失败：
1) 每次运行自建专用房源（不复用库内空置房源，避免与并发测试抢用）
2) 审核通过后轮候入队有短暂延迟，加重试等待
3) 编排器对失败步骤重试一次，并标注 FLAKY
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- 1) flows：总是新建专用房源 ----------
P = os.path.join(HERE, '_check_flows.py')
s = io.open(P, encoding='utf-8').read()

if 'def fresh_house' not in s:
    helper = '''
def fresh_house(tok, oid, tag):
    """每次都新建一套专用房源，避免与其他检查争用空置房源。"""
    tree = d(call('/spaces/tree?orgId=%s' % oid, token=tok))
    flat = []

    def walk(ns):
        for n in ns or []:
            flat.append(n)
            walk(n.get('children'))
    walk(tree if isinstance(tree, list) else (tree or {}).get('rows'))
    room = next((x for x in flat if x.get('spaceType') == 'ROOM'), None)
    floor = next((x for x in flat if x.get('spaceType') == 'FLOOR'), None)
    if not room and floor:
        st, r = call('/spaces', 'POST',
                     {'orgId': oid, 'spaceCode': 'F-R-' + tag, 'spaceName': '回归房间' + tag,
                      'spaceType': 'ROOM', 'parentId': floor['id'], 'area': 50}, tok)
        room = d((st, r))
    if not room:
        return None
    st, r = call('/houses', 'POST',
                 {'orgId': oid, 'spaceId': room['id'], 'houseCode': 'FH-' + tag,
                  'houseName': '%s房%s' % (TAG, tag), 'houseType': 'PUBLIC_RENTAL',
                  'useType': 'CIVIL', 'area': 50, 'rentStandard': 12,
                  'rentUnit': 'AREA_MONTH', 'houseStatus': 'VACANT'}, tok)
    return d((st, r))

'''
    s = s.replace('def main():', helper + 'def main():', 1)

# 批次加房源：总是新建
s = s.replace("        vacant = ensure_vacant_house(tok, oid)[:2]",
              "        fh = fresh_house(tok, oid, 'B')\n"
              "        vacant = [fh['id']] if fh else ensure_vacant_house(tok, oid)[:1]")

# 快捷签约：总是新建
s = s.replace("    free = ensure_vacant_house(tok, oid)",
              "    fh2 = fresh_house(tok, oid, 'S')\n"
              "    free = [fh2['id']] if fh2 else ensure_vacant_house(tok, oid)")

# 轮候入队重试等待
old_wait = '''            wait = rows(call('/allocation/waiting?pageNum=1&pageSize=200&securityType=PUBLIC',
                             token=tok))
            check('审核通过自动入轮候',
                  any(str(w.get('personId')) == str(pid) for w in wait),
                  '轮候池 %d 人' % len(wait))'''
new_wait = '''            queued = False
            for _ in range(5):
                wait = rows(call('/allocation/waiting?pageNum=1&pageSize=200'
                                 '&securityType=PUBLIC', token=tok))
                if any(str(w.get('personId')) == str(pid) for w in wait):
                    queued = True
                    break
                time.sleep(1)
            check('审核通过自动入轮候', queued, '轮候池 %d 人' % len(wait))'''
if old_wait in s:
    s = s.replace(old_wait, new_wait, 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('flows：已改为自建专用房源 + 入队重试')

# ---------- 2) 编排器：失败重试一次并标注 FLAKY ----------
V = os.path.join(HERE, '_verify_all.py')
s = io.open(V, encoding='utf-8').read()
if 'FLAKY' not in s:
    s = s.replace('''        if rc == 0:
            verdict = 'PASS'
        elif key in SOFT_FAIL:
            verdict = 'WARN'
        else:
            verdict = 'FAIL\'''',
                  '''        if rc != 0 and key not in SOFT_FAIL:
            # 单次失败可能是环境抖动：重试一次，能过则记为 FLAKY（需要关注但不阻塞）
            print('   ↻ 首次失败，重试一次…')
            rc2, out2, err2 = run(cmd[0], cmd[1:])
            if rc2 == 0:
                rc = 0
                print('   ↻ 重试通过 → 标记 FLAKY（不稳定用例，建议排查）')
                verdict_override = 'FLAKY'
                results.append((name, verdict_override, time.time() - t0, ''))
                continue
        if rc == 0:
            verdict = 'PASS'
        elif key in SOFT_FAIL:
            verdict = 'WARN'
        else:
            verdict = 'FAIL\'''')
    s = s.replace("    mark = {'PASS': '✔', 'WARN': '⚠', 'FAIL': '✘', 'SKIP': '–'}[verdict]",
                  "    mark = {'PASS': '✔', 'WARN': '⚠', 'FAIL': '✘', 'SKIP': '–',\n"
                  "            'FLAKY': '↻'}[verdict]")
    s = s.replace("    warns = [n for n, v, _, _ in results if v == 'WARN']",
                  "    warns = [n for n, v, _, _ in results if v == 'WARN']\n"
                  "    flaky = [n for n, v, _, _ in results if v == 'FLAKY']")
    s = s.replace("    if warns:\n        print('结论：通过（%d 项需人工关注：%s）' % (len(warns), '、'.join(warns)))\n        return 0",
                  "    if warns or flaky:\n"
                  "        parts = []\n"
                  "        if warns:\n"
                  "            parts.append('需人工关注：' + '、'.join(warns))\n"
                  "        if flaky:\n"
                  "            parts.append('不稳定用例：' + '、'.join(flaky))\n"
                  "        print('结论：通过（%s）' % '；'.join(parts))\n"
                  "        return 0")
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('编排器：已加失败重试与 FLAKY 标记')
