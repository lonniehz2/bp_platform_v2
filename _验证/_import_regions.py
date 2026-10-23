# -*- coding: utf-8 -*-
"""导入全国五级行政区划（省/市/区县/街道/社区村）到 bp_sys_region。

数据源：https://github.com/657258535/China-Area-Region-Administrative-Divisions
  province.json → 31 个省级
  China/<省名>.json → 该省五级树（code, name, children）

表结构：
  code       varchar(12) PK  行政区划代码（12 位）
  name       varchar(120)
  parent_code varchar(12)
  level      tinyint          1=省 2=市 3=区县 4=街道乡镇 5=社区村
  has_child  tinyint

用法：python _import_regions.py [--limit-village]
"""
import json
import sys
import urllib.parse
import urllib.request

import pymysql

BASE = ('https://raw.githubusercontent.com/657258535/'
        'China-Area-Region-Administrative-Divisions/master')
DB = dict(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
          database='bp_platform', charset='utf8mb4')
SKIP_VILLAGE = '--limit-village' not in sys.argv


def get(url):
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception:
            continue
    raise RuntimeError('下载失败: ' + url)


def main():
    conn = pymysql.connect(**DB)
    cur = conn.cursor()
    cur.execute('''
        create table if not exists bp_sys_region (
          code varchar(12) not null primary key,
          name varchar(120) not null,
          parent_code varchar(12) null,
          level tinyint not null,
          has_child tinyint not null default 0,
          key idx_parent (parent_code),
          key idx_level (level)
        ) default charset utf8mb4 comment='全国五级行政区划'
    ''')
    conn.commit()
    cur.execute('select count(*) from bp_sys_region')
    print('导入前已有', cur.fetchone()[0], '行')

    provinces = get(BASE + '/province.json')
    print('省级数据:', len(provinces))

    rows = []
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    def collect(node, parent, level):
        code = str(node.get('code') or '')
        if not code:
            return
        children = node.get('children') or []
        if level == 5 and SKIP_VILLAGE:
            return
        rows.append((code, node.get('name'), parent, level, 1 if children else 0))
        counts[level] = counts.get(level, 0) + 1
        for c in children:
            collect(c, code, level + 1)

    done = set()
    cur.execute('''select distinct r.name from bp_sys_region c
                join bp_sys_region r on r.code = c.parent_code where c.level = 2''')
    for (nm,) in cur.fetchall():
        done.add(nm)
    print('已导入省级:', len(done))

    for p in provinces:
        if p['name'] in done:
            continue
        for attempt in range(3):
            try:
                node = get(BASE + '/China/' + urllib.parse.quote(p['name']) + '.json')
                break
            except Exception as ex:
                print('  重试 %s（%s）' % (p['name'], ex))
                import time; time.sleep(3)
        else:
            print('  跳过（下载失败）:', p['name'])
            continue
        collect(node, None, 1)
        print('  %s 累计 %d 行' % (p['name'], len(rows)))
        if len(rows) >= 20000:
            cur.executemany('insert into bp_sys_region '
                            '(code,name,parent_code,level,has_child) values (%s,%s,%s,%s,%s) '
                            'on duplicate key update name=values(name)', rows)
            conn.commit()
            rows = []

    if rows:
        cur.executemany('insert into bp_sys_region '
                        '(code,name,parent_code,level,has_child) values (%s,%s,%s,%s,%s) '
                        'on duplicate key update name=values(name)', rows)
        conn.commit()

    cur.execute('select level, count(*) from bp_sys_region group by level order by level')
    print('\n各级数量:')
    for lv, n in cur.fetchall():
        print('  level %d: %d' % (lv, n))
    conn.close()
    print('导入完成')


if __name__ == '__main__':
    main()
