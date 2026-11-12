# 8090 升级专用

只允许操作：

```text
/home/luo/bp-platform-new
8090
```

绝对不修改：

```text
/opt/bp-platform
8080
```

## 升级前

```bash
export DB_PASSWORD='...'
cd /home/luo/bp-platform-new
./backup-8090.sh
```

必须在本地保留：

```text
数据库备份
multi-scene-platform.jar.<时间戳>
```

## 迁移

远程没有 mysql 客户端，不能直接执行 SQL。

使用本机 pymysql 连接：

```text
192.168.31.153:33306
bp_platform_v2
```

先备份，再执行 023–027。

本地执行迁移：

```bash
cd 多场景空间资产运营平台
DB_PASSWORD='...' python platform-deploy/remote/apply-8090-migrations.py
```

该脚本只执行 023–027，不包含 001–022。

## 替换 jar

```bash
cp multi-scene-platform.jar multi-scene-platform.jar.old
cp <新jar> multi-scene-platform.jar
```

## 重启

```bash
kill <8090 PID>
cd /home/luo/bp-platform-new
DB_PASSWORD='...' SERVER_PORT=8090 nohup java -Xms512m -Xmx1024m -XX:+UseG1GC   -Dfile.encoding=UTF-8 -jar multi-scene-platform.jar > app.log 2>&1 < /dev/null &
```

## 验证

```bash
PLATFORM_PASSWORD='...' ./verify-8090.sh
```

预期：

```text
GUARANTEE menus=10 roles>=4
ASSET menus=10 roles>=4
SERVICE menus=10 roles>=4
```

## 回滚

```bash
./rollback-8090.sh /home/luo/bp-platform-new/backup/multi-scene-platform.jar.<时间戳>
```

## 铁律

```text
1. 先备份数据库
2. 先备份 jar
3. 只重启 8090
4. 不触碰 8080
5. 迁移失败立即回滚 jar 和数据库
```
