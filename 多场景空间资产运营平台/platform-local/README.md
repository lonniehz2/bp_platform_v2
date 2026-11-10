# 本地开发数据库

## 前提

- Docker Desktop 已安装并启动
- 本地 3306 端口未被占用

## 启动

```powershell
cd platform-local
Copy-Item .env.example .env
.\scripts\db-local-up.ps1
```

首次启动会自动执行：

```text
platform-sql/001、002、018、019（003~017 仅用于旧库升级）
platform-local/seed/001_local_seed.sql
```

数据库连接：

```text
127.0.0.1:3306
数据库：bp_platform_v2
用户：root
密码：local123
```

## 启动后端

先构建 jar：

```powershell
platform-backend/scripts/package-with-web.ps1
```

再启动本地后端：

```powershell
platform-local/scripts/dev-backend.ps1
```

本地端口：8091，profile：local。

## 启动前端

```powershell
platform-local/scripts/dev-frontend.ps1
```

前端会把 /api 和 /actuator 代理到 8091。

## 本地验证

```powershell
platform-local/scripts/verify-local.ps1
```

预期：

```text
VERIFY OK: 168 assertions passed
```

## 重置

```powershell
platform-local/scripts/db-local-reset.ps1
```

会删除本地数据卷并重新执行 001、002、018、019 和 seed。

## 注意

- 本地库只用于开发，不替代远程联调库
- 不要把生产数据直接拷入本地
- 远程部署仍按批次执行

## 无 Docker 的本机 MySQL 回退

如果本机已有独立 MySQL，可指定端口和密码启动后端：

```powershell
platform-local/scripts/dev-backend.ps1 -DbPort 3307 -DbPassword ''
```

当前本机验证实例：

```text
MySQL 127.0.0.1:3307
后端 127.0.0.1:8091
```
