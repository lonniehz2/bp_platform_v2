# -*- coding: utf-8 -*-
"""同步 OpenAPI 下行清单与索引/18 号文档。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 1) OpenAPI：追加 token / 批量状态 / lock mode
p = os.path.join(ROOT, 'contracts', 'iot-callback.openapi.yaml')
s = io.open(p, encoding='utf-8').read()
if '/ymd/restful/lock/mode' not in s:
    s = s.rstrip() + '''
  - path: /ymd/restful/lock/mode
    method: POST
    status: 待 IoT 提供
    purpose: 常开/常闭/恢复（mode=OPEN|CLOSE|NORMAL，requestId 幂等）
    request:
      requestId: string
      lockId: string
      mode: string
    response:
      code: string
      message: string
      costMs: int
      data: { lockId: string, mode: string, effective: bool }
  - path: /ymd/restful/token
    method: POST
    status: 待 IoT 提供
    purpose: 取 Token / 续期（appId+timestamp+nonce+HMAC-SHA256 sign）
    request:
      appId: string
      timestamp: long
      nonce: string
      sign: string
    response:
      code: string
      data: { token: string, expiresIn: int, pwdSeed: string? }
  - path: /ymd/restful/device/status
    method: POST
    status: 待 IoT 提供
    purpose: 批量设备状态（lockIds ≤200，返回 online/battery/rssi/lastReportTime）
    request:
      lockIds: string[]
    response:
      code: string
      data:
        - { lockId: string, online: bool, battery: int, rssi: int,
            lastReportTime: string, firmware: string? }
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('OpenAPI 下行清单已补 3 项')

# 2) 索引
p = os.path.join(ROOT, '00_文档包索引与评审台账.md')
s = io.open(p, encoding='utf-8').read()
if '21_IoT侧需求规格说明书' not in s:
    m = re.search(r'^.*20_IoT联调上线切换清单\.md.*$', s, re.M)
    if m:
        line = m.group(0)
        s = s.replace(line, line + '\n| 21 | [21_IoT侧需求规格说明书.md](21_IoT侧需求规格说明书.md) | 5 个待实现能力的接口规格与验收标准 | 联调 |', 1)
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        print('索引已补 21')

# 3) 18 号：回链 21
p = os.path.join(ROOT, '18_IoT平台需增加或完善的内容清单.md')
s = io.open(p, encoding='utf-8').read()
if '21_IoT侧需求规格说明书' not in s:
    s = s.rstrip() + '''

---

## 附二：未实现项的接口规格

第 1/2/3/5 项（Token、批量状态、lock/mode、表计口径、压测环境）的**接口与验收规格**
见 [21_IoT侧需求规格说明书.md](21_IoT侧需求规格说明书.md)。
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('18 已回链 21')
