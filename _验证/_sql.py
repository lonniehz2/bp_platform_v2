# -*- coding: utf-8 -*-
"""通过 SSH 在 VM 上执行 SQL（Windows 直连 MySQL 偶尔被断，改走跳板）。

用法：
  python _sql.py "select 1"
  python _sql.py --file script.sql
"""
import os
import sys

import paramiko

HOST = os.environ.get('VM_HOST', '192.168.31.11')
USER = os.environ.get('VM_USER', 'luo')
PWD = os.environ.get('VM_PWD', 'hzbit56771010')

DB_HOST = os.environ.get('DB_HOST', '192.168.31.153')
DB_PORT = os.environ.get('DB_PORT', '33306')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PWD = os.environ.get('DB_PWD', '5677@Mysql')
DB_NAME = os.environ.get('DB_NAME', 'bp_platform')


def run_sql(sql: str) -> str:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, 22, USER, PWD, timeout=20, banner_timeout=20)
    try:
        cmd = ("mysql -h%s -P%s -u%s -p'%s' %s -e %s"
               % (DB_HOST, DB_PORT, DB_USER, DB_PWD, DB_NAME,
                  _quote(sql)))
        _in, out, err = client.exec_command(cmd, timeout=180)
        stdout = out.read().decode('utf-8', 'replace')
        stderr = err.read().decode('utf-8', 'replace')
        return stdout + (('\n[stderr] ' + stderr) if stderr.strip() else '')
    finally:
        client.close()


def _quote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"


if __name__ == '__main__':
    if '--file' in sys.argv:
        path = sys.argv[sys.argv.index('--file') + 1]
        sql = open(path, encoding='utf-8').read()
    else:
        sql = sys.argv[1]
    print(run_sql(sql))
