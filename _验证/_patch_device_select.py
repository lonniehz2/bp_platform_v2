# -*- coding: utf-8 -*-
"""设备/门锁输入换 DeviceSelect。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

TARGETS = {
    'Grants.vue': [('lockId', '240px')],
    'DevCommands.vue': [('query.deviceId', '240px')],
    'DevEvents.vue': [('query.deviceId', '240px')],
    'MeterReadings.vue': [('rf.deviceId', '100%')],
}

for fname, models in TARGETS.items():
    p = os.path.join(VIEWS, fname)
    s = io.open(p, encoding='utf-8').read()
    total = 0
    for model, width in models:
        pattern = re.compile(
            r'<el-input[^>]*v-model="%s"[^>]*?/>' % re.escape(model), re.S)
        def repl(m, w=width, mod=model):
            return '<DeviceSelect v-model="%s" width="%s" testid="device-select" />' % (mod, w)
        s, n = pattern.subn(repl, s)
        total += n
    if total and ('import DeviceSelect' not in s):
        s = s.replace("import req from '@/api/request'",
                      "import req from '@/api/request'\nimport DeviceSelect from '@/components/DeviceSelect.vue'", 1)
    if total:
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print(fname, '替换', total)
