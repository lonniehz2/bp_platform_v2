# 生产前基线（本地）

- 日期：2026-11-12
- 提交：172f957
- 环境：本机 8091 + Docker MySQL
- 发布包：`platform-deploy/release/bp-platform-20261112-025342.zip`
- 发布包 SHA256：`5435ca575d3d896af9e644b1b52aa2141d58a0b4bbbcea71c4368ae4ff15af63`

## 性能基线

实测：

```text
login + menu-tree = 183 ms
menus = 10
projects = 4
```

这是本地基线，不代表生产网络/数据库性能。

## 健康检查

```text
GET /actuator/health = 200
```

## 发布包内容

```text
app.jar
web/
platform-sql/
platform-deploy/
version.txt
```

## 脚本校验

以下脚本已通过 `bash -n`：

```text
backup-db.sh
migrate-db.sh
restore-db.sh
security-check.sh
smoke-prod.sh
```

## 安全结论

发布前必须修改：

```text
1. admin 默认密码
2. AUTH_SECRET（当前默认 dev-only-change-me）
3. DB_PASSWORD
```

必须保证：

```text
1. /etc/bp-platform.env 权限 600
2. 8091 只监听 127.0.0.1 或内网
3. 公网只暴露 Nginx 80/443
4. 上传目录有备份
5. 数据库每日备份
```

## CORS 约束

当前 CORS 只允许：

```text
http://localhost:*
http://127.0.0.1:*
```

生产部署必须让前端和 API 同源：

```text
https://bp.example.com/       -> web
https://bp.example.com/api/   -> 8091
```

如果前端与 API 使用不同域名，需要先修改 `WebConfig` 的 CORS 配置，并重新发布。

## 未验证项

```text
真实 HTTPS 证书
真实 Nginx 配置加载
真实 MySQL 生产账号
真实服务器防火墙
真实浏览器下载落盘
```

这些需要在预发服务器上完成。
