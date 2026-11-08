import paramiko
local=r'D:\Work\业务平台开发\多场景空间资产运营平台\platform-backend\scripts\DbBackup.class'
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy()); c.connect('192.168.31.11',username='luo',password='hzbit56771010',timeout=15)
sftp=c.open_sftp(); sftp.put(local,'/home/luo/bp-platform-new/DbBackup.class'); sftp.close()
out='/home/luo/bp-platform-new/backup/bp_platform_v2_manual.sql'
cmd=f"cd /home/luo/bp-platform-new && java -cp mysql-connector-j-8.3.0.jar:. DbBackup 192.168.31.153 33306 root '5677@Mysql' bp_platform_v2 {out} && gzip -f {out} && ls -lh {out}.gz"
_,o,e=c.exec_command(cmd,timeout=300); print(o.read().decode()); print(e.read().decode()[:1200]); print('exit',o.channel.recv_exit_status()); c.close()
