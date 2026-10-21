# -*- coding: utf-8 -*-
"""公司网络环境探测"""
import socket

for name, host, port in (
        ('VM 应用', '192.168.31.11', 8080),
        ('VM SSH', '192.168.31.11', 22),
        ('MySQL', '192.168.31.153', 33306)):
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.close()
        print('  %-10s %s:%s  OK' % (name, host, port))
    except Exception as e:
        print('  %-10s %s:%s  FAIL %s' % (name, host, port, type(e).__name__))
