# -*- coding: utf-8 -*-
"""以 root 身份在 VM 上执行任意命令（走 su 交互，解决 luo 无 sudo 的问题）

用法：python _root_cmd.py "<命令>"
"""
import sys
import time

import paramiko

HOST = '192.168.31.11'
USER = 'luo'
PWD = 'hzbit56771010'
ROOT_PWD = 'hzbit56771010'


class Shell:
    def __init__(self, client):
        self.ch = client.invoke_shell(width=240, height=80)
        self.buf = ''
        self.drain(1.0)

    def drain(self, seconds=1.0):
        end = time.time() + seconds
        while time.time() < end:
            if self.ch.recv_ready():
                self.buf += self.ch.recv(65535).decode('utf-8', 'replace')
                end = time.time() + 0.3
            else:
                time.sleep(0.1)
        out, self.buf = self.buf, ''
        return out

    def send(self, cmd, seconds=2.0):
        self.ch.send(cmd + '\n')
        return self.drain(seconds)

    def expect(self, needles, timeout=15):
        end = time.time() + timeout
        acc = ''
        while time.time() < end:
            acc += self.drain(0.4)
            for n in needles:
                if n in acc:
                    return acc
        return acc


def main():
    if len(sys.argv) < 2:
        print('用法: python _root_cmd.py "<命令>"')
        return 2
    cmd = sys.argv[1]

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=22, username=USER, password=PWD, timeout=20,
              banner_timeout=30, auth_timeout=30,
              look_for_keys=False, allow_agent=False)
    try:
        sh = Shell(c)
        out = sh.send('su -', 2.0)
        out += sh.expect(['密码', 'assword', '口令', 'Password'], 20)
        if '密码' not in out and 'assword' not in out and '口令' not in out and 'Password' not in out:
            print('未出现密码提示：%r' % out[-300:])
            return 1
        sh.send(ROOT_PWD, 4.0)
        ok = sh.send('id -un', 3.0)
        if 'root' not in ok:
            ok += sh.send('id -un', 3.0)
        if 'root' not in ok:
            print('提权失败：%r' % ok[-300:])
            return 1
        # 用分隔符包住输出，便于截取
        sh.send('echo __BEGIN__', 1.0)
        res = sh.send(cmd, 8.0)   # ← 必须接住返回值，否则命令输出丢失
        res += sh.send('echo __DONE__', 2.0)
        print(res)
        return 0
    finally:
        c.close()


if __name__ == '__main__':
    sys.exit(main())
