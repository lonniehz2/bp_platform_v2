ROOTPW='hzbit56771010'
export LANG=C LC_ALL=C

echo "===== 1. 部署 jar ====="
echo "$ROOTPW" | su - root -c "
mv /tmp/bp-platform.jar /opt/bp-platform/bp-platform.jar
chown bp:bp /opt/bp-platform/bp-platform.jar
chmod 640 /opt/bp-platform/bp-platform.jar
ls -lh /opt/bp-platform/bp-platform.jar
"

echo
echo "===== 2. 写入环境变量文件（含密码，权限 600）====="
echo "$ROOTPW" | su - root -c "cat > /etc/bp-platform.env <<'EOF'
# ===== 业务平台运行环境 =====
# 数据库（独立 MySQL 服务器）
BP_DB_HOST=192.168.31.153
BP_DB_PORT=33306
BP_DB_USER=root
BP_DB_PWD=5677@Mysql
BP_DB_NAME=bp_platform

# Redis（本机）
BP_REDIS_HOST=127.0.0.1
BP_REDIS_PORT=6379
BP_REDIS_PWD=bpRedis2026

# RabbitMQ（本机）
BP_MQ_HOST=127.0.0.1
BP_MQ_PORT=5672
BP_MQ_USER=bp
BP_MQ_PWD=bpMq2026

# 健康检查：数据库探针默认关闭（避免启动时阻塞），需要时改 true
BP_HEALTH_DB=false

# 雪花ID（单实例）
BP_WORKER_ID=1
BP_DATACENTER_ID=1

# IoT 凭证（待填）
YMD_APP_ID=
YMD_APP_SECRET=
YMD_KEY_VERSION=k1
EOF
chmod 600 /etc/bp-platform.env
chown root:root /etc/bp-platform.env
echo '  /etc/bp-platform.env 已写入 (600)'"

echo
echo "===== 3. 写入 systemd 服务 ====="
echo "$ROOTPW" | su - root -c "cat > /etc/systemd/system/bp-platform.service <<'EOF'
[Unit]
Description=Yundao Business Platform
Documentation=file:/opt/bp-platform/README.md
After=network-online.target redis-server.service rabbitmq-server.service
Wants=network-online.target

[Service]
Type=simple
User=bp
Group=bp
EnvironmentFile=/etc/bp-platform.env
WorkingDirectory=/opt/bp-platform
ExecStart=/usr/bin/java -Xms512m -Xmx1024m -XX:+UseG1GC -Dfile.encoding=UTF-8 -jar /opt/bp-platform/bp-platform.jar --server.port=8080
SuccessExitStatus=143
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/bp-platform/app.log
StandardError=append:/var/log/bp-platform/err.log

# 安全加固
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
echo '  systemd 单元已创建'"

echo
echo "===== 4. 启动服务 ====="
echo "$ROOTPW" | su - root -c "systemctl enable bp-platform 2>&1 | tail -2; systemctl start bp-platform"
sleep 25

echo
echo "===== 5. 服务状态 ====="
systemctl is-active bp-platform
echo "$ROOTPW" | su - root -c "systemctl status bp-platform --no-pager 2>&1 | head -12"

echo
echo "===== 6. 应用日志 ====="
echo "$ROOTPW" | su - root -c "tail -25 /var/log/bp-platform/app.log 2>/dev/null; tail -10 /var/log/bp-platform/err.log 2>/dev/null"
