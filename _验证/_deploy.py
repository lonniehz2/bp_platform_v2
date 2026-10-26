# -*- coding: utf-8 -*-
"""部署 bp-platform：上传 jar（可选）→ su 提权 → 重启服务 → 健康检查

用法：
  python _deploy.py                 # 只用已上传的 /tmp/bp-platform.jar
  python _deploy.py --upload <jar>  # 先上传再部署
"""
import hashlib
import os
import re
import sys
import time

import paramiko

HOST = os.environ.get('VM_HOST', '192.168.31.11')
PORT = int(os.environ.get('VM_PORT', '22'))
USER = os.environ.get('VM_USER', 'luo')
PWD = os.environ.get('VM_PWD', 'hzbit56771010')
ROOT_PWD = os.environ.get('VM_ROOT_PWD', 'hzbit56771010')
JAR_REMOTE = '/tmp/bp-platform.jar'
JAR_TARGET = '/opt/bp-platform/bp-platform.jar'


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def remote_sha256(client, path):
    _i, o, _e = client.exec_command('sha256sum %s' % path, timeout=300)
    out = o.read().decode('utf-8', 'replace').strip()
    return out.split()[0] if out else ''


def upload(client, local):
    sftp = client.open_sftp()
    size = os.path.getsize(local)
    print('上传 %s (%.1f MB) -> %s' % (local, size / 1048576, JAR_REMOTE))
    sftp.put(local, JAR_REMOTE)
    remote = sftp.stat(JAR_REMOTE).st_size
    print('  远程大小 %.1f MB' % (remote / 1048576))
    sftp.close()
    # 上传完整性校验：jar 被截断会导致 "Invalid or corrupt jarfile" 且服务起不来
    if remote != size:
        raise RuntimeError('上传不完整：本地 %d 字节，远程 %d 字节（差 %d）；请重试上传'
                           % (size, remote, size - remote))
    # 大小一致仍可能内容损坏（曾出现 jar 起不来）：比对 SHA-256
    local_sha = sha256_of(local)
    remote_hash = remote_sha256(client, JAR_REMOTE)
    if remote_hash and local_sha != remote_hash:
        raise RuntimeError('上传内容校验失败：本地 %s，远程 %s；请重试上传'
                           % (local_sha[:16], remote_hash[:16]))
    print('  上传校验通过 sha256=%s' % local_sha[:16])


def verify_replaced(client, local):
    """部署后校验：远端 jar 大小必须与本地一致，否则视为未替换（历史踩坑）。"""
    sftp = client.open_sftp()
    try:
        remote = sftp.stat(JAR_TARGET).st_size
    finally:
        sftp.close()
    local_size = os.path.getsize(local)
    if remote != local_size:
        raise RuntimeError('部署未生效：远端 %s 为 %d 字节，本地 %d 字节'
                           % (JAR_TARGET, remote, local_size))
    print('部署校验通过：远端 jar %d 字节与本地一致' % remote)


class Shell:
    def __init__(self, client):
        self.ch = client.invoke_shell(width=200, height=50)
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
            low = acc.lower()
            for n in needles:
                if n in acc or n.lower() in low:
                    return acc
        return acc

    def close(self):
        try:
            self.ch.close()
        except Exception:
            pass


def main():
    args = sys.argv[1:]
    local_jar = None
    if len(args) >= 2 and args[0] == '--upload':
        local_jar = args[1]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PWD, timeout=20,
                   banner_timeout=30, auth_timeout=30,
                   look_for_keys=False, allow_agent=False)
    try:
        if local_jar:
            upload(client, local_jar)
        else:
            sftp = client.open_sftp()
            try:
                sftp.stat(JAR_REMOTE)
            except IOError:
                print('错误：%s 不存在，请用 --upload <jar> 指定待部署文件' % JAR_REMOTE)
                return 1
            finally:
                sftp.close()

        sh = Shell(client)
        out = sh.send('su -', 1.5)
        out += sh.expect(['assword', '密码', '口令', 'Password'])
        if 'assword' not in out and '密码' not in out and '口令' not in out and 'Password' not in out:
            print('未出现密码提示，输出：%s' % out[-400:])
            sh.close()
            return 1
        out = sh.send(ROOT_PWD, 4.0)
        out += sh.send('id -un', 3.0)
        if 'root' not in out:
            out += sh.send('id -un', 3.0)
        if 'root' not in out:
            print('提权失败，原始输出：%r' % out[-600:])
            sh.close()
            return 1
        print('已提权 root')

        steps = [
            ('停止服务', 'systemctl stop bp-platform', 3),
            ('替换 jar', 'mv -f %s %s && chown bp:bp %s' % (JAR_REMOTE, JAR_TARGET, JAR_TARGET), 2),
            ('启动服务', 'systemctl start bp-platform', 2),
            ('服务状态', 'systemctl is-active bp-platform', 2),
        ]
        for name, cmd, wait in steps:
            outp = sh.send(cmd, wait)
            line = ' '.join(outp.split())
            print('%-8s %s' % (name, line[-160:]))
        sh.close()

        # 轮询健康检查（最多 60 秒）
        health_code = ''
        for _i in range(20):
            time.sleep(3)
            _in, out, _err = client.exec_command(
                'curl -s -o /dev/null -w %{http_code} '
                'http://127.0.0.1:8080/actuator/health', timeout=15)
            health_code = out.read().decode().strip()
            if health_code == '200':
                break
        print('%-8s %s' % ('健康检查', health_code or '无响应'))
        if health_code != '200':
            print('健康检查未通过（%s），请查看服务日志' % (health_code or '无响应'))
            return 1
        # 关键：确认 jar 真的被替换（历史上出现过「提权成功但 jar 未换」）
        if local_jar:
            verify_replaced(client, local_jar)
        return 0
    finally:
        client.close()


if __name__ == '__main__':
    sys.exit(main())
