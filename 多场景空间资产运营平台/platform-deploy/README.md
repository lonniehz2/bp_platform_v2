# 生产部署 Runbook

## 1. 目标结构

```text
/opt/bp-platform/
  app.jar
  web/
  uploads/
  logs/
  backups/
  version.txt
/etc/bp-platform.env
```

## 2. 首次部署

```bash
sudo useradd -r -s /bin/false bp-platform || true
sudo mkdir -p /opt/bp-platform/{web,uploads,logs,backups}
sudo chown -R bp-platform:bp-platform /opt/bp-platform
sudo cp platform-deploy/env.example /etc/bp-platform.env
sudo chmod 600 /etc/bp-platform.env
# 修改 DB、AUTH_SECRET、密码后：
# 首次登录后立即修改 admin 默认密码（或使用正式初始化账号）
sudo cp platform-deploy/systemd/bp-platform.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now bp-platform
```

Nginx：

```bash
sudo cp platform-deploy/nginx/bp-platform.conf /etc/nginx/conf.d/bp-platform.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 3. 数据库迁移

必须先备份：

```bash
export DB_NAME=bp_platform_v2 DB_USER=bp_platform DB_PASSWORD=...
platform-deploy/scripts/backup-db.sh
platform-deploy/scripts/migrate-db.sh
```

迁移后校验：

```bash
cd 多场景空间资产运营平台/platform-frontend
PLATFORM_BASE=https://bp.example.com PLATFORM_USER=admin PLATFORM_PASSWORD=... node scripts/check-scene-data.mjs
```

## 4. 发布新版本

```bash
sudo systemctl stop bp-platform
sudo cp app.jar /opt/bp-platform/app.jar.new
sudo cp -r web/* /opt/bp-platform/web/
sudo mv /opt/bp-platform/app.jar.new /opt/bp-platform/app.jar
sudo chown -R bp-platform:bp-platform /opt/bp-platform
sudo systemctl start bp-platform
curl -fsS https://bp.example.com/actuator/health
```

## 5. 回滚

```bash
sudo systemctl stop bp-platform
sudo cp /opt/bp-platform/backups/app.jar.previous /opt/bp-platform/app.jar
sudo systemctl start bp-platform
```

数据库回滚只在确认迁移造成不可恢复问题时执行：

```bash
platform-deploy/scripts/restore-db.sh /opt/bp-platform/backups/bp_platform_v2_YYYYMMDD_HHMMSS.sql.gz
```

## 6. 安全检查

```bash
set -a; . /etc/bp-platform.env; set +a
platform-deploy/scripts/security-check.sh
```

必须确认：

```text
AUTH_SECRET 不是默认值
DB_PASSWORD 不是 local123
/etc/bp-platform.env 权限 600
8091 不直接暴露公网
上传目录存在
```

## 7. 健康与性能

```bash
curl -fsS https://bp.example.com/actuator/health
BASE_URL=https://bp.example.com PLATFORM_PASSWORD=... platform-deploy/scripts/smoke-prod.sh
```

## 8. 日常备份

```cron
0 2 * * * DB_NAME=bp_platform_v2 DB_USER=bp_platform DB_PASSWORD=... /opt/bp-platform/scripts/backup-db.sh >> /opt/bp-platform/logs/backup.log 2>&1
```

备份保留 14 天。

## 9. 发布检查清单

```text
[ ] 数据库已备份
[ ] AUTH_SECRET 已更换
[ ] admin 密码已更换
[ ] 001–027 迁移完成
[ ] health 通过
[ ] 三场景菜单/角色通过
[ ] 中文/英文登录通过
[ ] 报表下载通过
[ ] 8091 未暴露公网
[ ] 回滚 jar 已保留
```
