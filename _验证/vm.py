# -*- coding: utf-8 -*-
"""
VM 远程执行助手（paramiko）
用法：
  python vm.py "<命令>"          执行单条命令
  python vm.py -f script.sh      执行本地脚本
环境变量：
  VM_HOST / VM_USER / VM_PWD / VM_PORT
"""
import os
import sys

import paramiko

HOST = os.environ.get('VM_HOST', '192.168.31.11')
PORT = int(os.environ.get('VM_PORT', '22'))
USER = os.environ.get('VM_USER', 'luo')
PWD = os.environ.get('VM_PWD', 'hzbit56771010')
CMD_TIMEOUT = int(os.environ.get('VM_TIMEOUT', '180'))


def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PWD,
              timeout=15, banner_timeout=20, auth_timeout=20,
              look_for_keys=False, allow_agent=False)
    return c


def run(cmd, timeout=None):
    c = connect()
    try:
        t = timeout if timeout is not None else CMD_TIMEOUT
        stdin, stdout, stderr = c.exec_command(cmd, timeout=t, get_pty=False)
        out = stdout.read().decode('utf-8', 'replace')
        err = stderr.read().decode('utf-8', 'replace')
        code = stdout.channel.recv_exit_status()
        return code, out, err
    finally:
        c.close()


def main():
    if len(sys.argv) < 2:
        print('用法: python vm.py "<命令>"  或  python vm.py -f <脚本>')
        return 2
    if sys.argv[1] == '-f':
        cmd = open(sys.argv[2], encoding='utf-8').read()
    else:
        cmd = sys.argv[1]
    code, out, err = run(cmd)
    if out:
        sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return code


if __name__ == '__main__':
    sys.exit(main())
