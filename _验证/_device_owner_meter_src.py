# -*- coding: utf-8 -*-
"""1) 设备责任主体（owner_org_id / maintain_org_id）
2) 抄表读数计量溯源（device_id）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- 设备实体 ----------
D = os.path.join(J, 'dev', 'entity', 'DevDevice.java')
s = io.open(D, encoding='utf-8').read()
if 'private Long ownerOrgId' not in s:
    s = s.replace('    private Long orgId;',
                  '    private Long orgId;\n\n'
                  '    /** 产权方组织（设备归谁所有） */\n'
                  '    private Long ownerOrgId;\n\n'
                  '    /** 维保方组织（谁负责维修） */\n'
                  '    private Long maintainOrgId;', 1)
    io.open(D, 'w', encoding='utf-8', newline='').write(s)
    print('DevDevice：ownerOrgId / maintainOrgId 已加')

# ---------- 抄表实体 ----------
M = os.path.join(J, 'fin', 'entity', 'FinMeterReading.java')
s = io.open(M, encoding='utf-8').read()
if 'private String deviceId' not in s:
    s = s.replace('    private Long feeItemId;',
                  '    private Long feeItemId;\n\n'
                  '    /** 计量来源设备（用于溯源，可为空=人工录入） */\n'
                  '    private String deviceId;', 1)
    io.open(M, 'w', encoding='utf-8', newline='').write(s)
    print('FinMeterReading：deviceId 已加')

# ---------- 抄表命令 ----------
C = os.path.join(J, 'fin', 'dto', 'MeterReadingCmd.java')
s = io.open(C, encoding='utf-8').read()
if 'deviceId' not in s:
    s = s.replace('        LocalDate readDate,', '        LocalDate readDate,\n        String deviceId,', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('MeterReadingCmd：deviceId 已加')

# ---------- 抄表服务写入 ----------
I = os.path.join(J, 'fin', 'service', 'impl', 'MeterReadingServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'setDeviceId' not in s:
    s = s.replace('        e.setReading(cmd.reading());',
                  '        e.setReading(cmd.reading());\n'
                  '        e.setDeviceId(cmd.deviceId());', 1)
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('MeterReadingServiceImpl：写入 deviceId')

print('完成')
