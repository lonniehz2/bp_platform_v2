# -*- coding: utf-8 -*-
"""查看远端 jar 与进程状态，确认部署是否真的替换。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.31.11', 22, 'luo', 'hzbit56771010', timeout=20, banner_timeout=20)
cmds = [
    'ls -l /opt/bp-platform/',
    "stat -c '%y %s' /opt/bp-platform/bp-platform.jar",
    "ps -eo pid,lstart,cmd | grep bp-platform.jar | grep -v grep",
    "unzip -l /opt/bp-platform/bp-platform.jar 2>/dev/null | grep -c 'Arrears-'",
]
for cmd in cmds:
    _in, out, err = c.exec_command(cmd, timeout=60)
    print('$', cmd)
    print(out.read().decode('utf-8', 'replace')[:400])
    e = err.read().decode('utf-8', 'replace')
    if e.strip():
        print('  [err]', e[:200])
c.close()
