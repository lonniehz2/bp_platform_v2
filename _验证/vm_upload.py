# -*- coding: utf-8 -*-
"""上传文件到 VM（SFTP）"""
import os
import sys

import paramiko

HOST = os.environ.get('VM_HOST', '192.168.31.11')
PORT = int(os.environ.get('VM_PORT', '22'))
USER = os.environ.get('VM_USER', 'luo')
PWD = os.environ.get('VM_PWD', 'hzbit56771010')


def main():
    if len(sys.argv) < 3:
        print('用法: python vm_upload.py <本地路径> <远程路径>')
        return 2
    local, remote = sys.argv[1], sys.argv[2]

    if not os.path.exists(local):
        print('本地文件不存在: %s' % local)
        return 1

    size = os.path.getsize(local)
    print('上传: %s (%.1f MB) -> %s' % (local, size / 1024 / 1024, remote))

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PWD,
              timeout=20, banner_timeout=30, auth_timeout=30,
              look_for_keys=False, allow_agent=False)
    try:
        sftp = c.open_sftp()
        # 进度回调
        last = [0]

        def cb(done, total):
            pct = int(done * 100 / total) if total else 0
            if pct >= last[0] + 10:
                last[0] = pct
                print('  %d%%' % pct)

        sftp.put(local, remote, callback=cb)
        st = sftp.stat(remote)
        print('完成，远程大小 %.1f MB' % (st.st_size / 1024 / 1024))
        sftp.close()
    finally:
        c.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
