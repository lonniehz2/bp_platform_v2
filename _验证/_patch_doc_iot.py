# -*- coding: utf-8 -*-
import io

p = r'..\_验证\_doc_cq.md'
s = io.open(p, encoding='utf-8').read()
s = s.replace('- IoT `read-now` 接口列入待接入事项；当前调用返回明确提示，人工抄表可用；',
              '- IoT `read-now` 适配器已就绪：配置 `bp.iot.read-now-url` 与 `bp.iot.token` 后直接调用；未配置或设备离线时提示人工抄表；')
s = s.replace('| 设备抄表 | 409「IoT read-now 接口待接入，请使用人工抄表」 |',
              '| 设备抄表 | 未配置时 409「IoT read-now 接口未配置，请使用人工抄表」；配置后走 IoT |')
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('doc updated')
