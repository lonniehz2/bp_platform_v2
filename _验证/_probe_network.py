# -*- coding: utf-8 -*-
"""家庭网络环境探测：可达性 + 主机资源"""
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request

results = []


def tcp(host, port, timeout=4):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True, ''
    except Exception as e:
        return False, type(e).__name__


def http(url, timeout=8, headers=None):
    try:
        r = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(r, timeout=timeout) as x:
            body = x.read(600)
            return True, body[:200].decode('utf-8', 'replace').replace('\n', ' ')
    except urllib.error.HTTPError as e:
        return True, 'HTTP %s' % e.code
    except Exception as e:
        return False, type(e).__name__


print('=' * 76)
print(' 家庭网络环境探测')
print('=' * 76)

# ---- 内网 ----
ok, err = tcp('192.168.31.11', 8080)
print('  VM 应用 192.168.31.11:8080      %s' % ('OK' if ok else 'FAIL ' + err))
ok2, err2 = tcp('192.168.31.11', 22)
print('  VM SSH  192.168.31.11:22        %s' % ('OK' if ok2 else 'FAIL ' + err2))
ok3, err3 = tcp('192.168.31.153', 33306)
print('  MySQL   192.168.31.153:33306    %s' % ('OK' if ok3 else 'FAIL ' + err3))

if ok:
    okh, txt = http('http://192.168.31.11:8080/actuator/health')
    print('  VM 健康检查                     %s' % (txt if okh else 'FAIL'))

# ---- 外网 ----
print()
for name, url in (
        ('IoT 平台（api.hzbit.cn:4443）', 'https://api.hzbit.cn:4443/'),
        ('Maven 中央仓库', 'https://repo.maven.apache.org/maven2/'),
        ('npm registry', 'https://registry.npmjs.org/'),
        ('阿里云镜像', 'https://maven.aliyun.com/repository/public/'),
):
    ok, txt = http(url)
    print('  %-32s %s' % (name, 'OK' if ok else 'FAIL ' + txt))

# ---- 主机资源（决定能否跑单测）----
print()
try:
    ps = subprocess.run(
        ['powershell', '-NoProfile', '-Command',
         "$os=Get-CimInstance Win32_OperatingSystem; "
         "Write-Output ('{0}|{1}' -f $os.TotalVisibleMemorySize, $os.FreePhysicalMemory)"],
        capture_output=True, text=True, timeout=40)
    total_kb, free_kb = ps.stdout.strip().split('|')
    total_gb = int(total_kb) / 1024 / 1024
    free_gb = int(free_kb) / 1024 / 1024
    print('  主机内存：总 %.1f GB，可用 %.1f GB' % (total_gb, free_gb))
    print('  单元测试（Mockito）可行性：%s'
          % ('可行（可用 ≥2GB）' if free_gb >= 2 else '仍不足（需 ≥2GB）'))
except Exception as e:
    print('  主机内存探测失败：%s' % e)
