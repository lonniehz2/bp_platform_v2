# -*- coding: utf-8 -*-
"""让「先查后写」扫描读取人工复核清单：仅未复核的高风险项才算失败。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_check_race_pattern.py')
s = io.open(P, encoding='utf-8').read()

if 'REVIEWED_FILE' in s:
    print('已支持复核清单')
    raise SystemExit(0)

s = s.replace('''import os
import re
import sys''', '''import json
import os
import re
import sys''')

s = s.replace('''ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))''',
'''HERE = os.path.dirname(os.path.abspath(__file__))
REVIEWED_FILE = os.path.join(HERE, '_race_reviewed.json')


def load_reviewed():
    """已人工复核的条目（class.method）。"""
    if not os.path.exists(REVIEWED_FILE):
        return set()
    try:
        data = json.load(io.open(REVIEWED_FILE, encoding='utf-8'))
    except Exception:
        return set()
    return {x['item'] for x in data.get('reviewed', []) if x.get('item')}


ROOT = os.path.abspath(os.path.join(HERE, '..'))''')

s = s.replace('''                level = classify(rel, name, body)
                buckets[level].append('%s:%d  %s.%s'
                                      % (rel.replace('backend/src/main/java/com/yundao/bp/', ''),
                                         line, cls, name))''',
'''                level = classify(rel, name, body)
                key = '%s.%s' % (cls, name)
                if level == 'HIGH' and key in REVIEWED:
                    buckets['LOW'].append('%s:%d  %s（已复核）' % (
                        rel.replace('backend/src/main/java/com/yundao/bp/', ''), line, key))
                    continue
                buckets[level].append('%s:%d  %s.%s'
                                      % (rel.replace('backend/src/main/java/com/yundao/bp/', ''),
                                         line, cls, name))''')

s = s.replace('''def main():
    buckets = {'HIGH': [], 'MED': [], 'LOW': []}''',
'''def main():
    REVIEWED = load_reviewed()
    buckets = {'HIGH': [], 'MED': [], 'LOW': []}''')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('扫描器已支持人工复核清单')
