export LANG=C LC_ALL=C
ROOTPW='hzbit56771010'

echo "===== 1. 服务状态总览 ====="
for s in bp-platform redis-server rabbitmq-server; do
  a=$(systemctl is-active $s 2>/dev/null)
  e=$(systemctl is-enabled $s 2>/dev/null)
  printf "  %-18s active=%-8s enabled=%s\n" "$s" "$a" "$e"
done

echo
echo "===== 2. 端口监听 ====="
ss -lntp 2>/dev/null | awk 'NR==1 || /:8080|:6379|:5672|:15672/ {print "  "$0}'

echo
echo "===== 3. 应用健康（VM 本地）====="
curl -s -m 10 http://127.0.0.1:8080/actuator/health; echo

echo
echo "===== 4. Redis 连接（用应用配置的密码）====="
redis-cli -a 'bpRedis2026' --no-auth-warning ping
redis-cli -a 'bpRedis2026' --no-auth-warning dbsize
echo "  Redis 内存:"
redis-cli -a 'bpRedis2026' --no-auth-warning info memory 2>/dev/null | grep -E "used_memory_human|maxmemory_human"

echo
echo "===== 5. RabbitMQ 队列/连接 ====="
echo "$ROOTPW" | su - root -c "rabbitmqctl list_queues name messages consumers 2>&1 | head -8"
echo "  连接数:"
echo "$ROOTPW" | su - root -c "rabbitmqctl list_connections name state 2>&1 | head -6"

echo
echo "===== 6. 应用日志中的错误（最近 30 行过滤 ERROR/WARN）====="
echo "$ROOTPW" | su - root -c "grep -E 'ERROR|WARN' /var/log/bp-platform/app.log 2>/dev/null | tail -10; grep -c ERROR /var/log/bp-platform/app.log 2>/dev/null | sed 's/^/  ERROR 计数: '/"
echo "--- err.log ---"
echo "$ROOTPW" | su - root -c "tail -5 /var/log/bp-platform/err.log 2>/dev/null || echo '  (空)'"

echo
echo "===== 7. 资源占用 ====="
free -h | head -2
echo "-- 各服务内存 --"
echo "$ROOTPW" | su - root -c "systemctl show bp-platform redis-server rabbitmq-server -p MemoryCurrent 2>/dev/null | paste - - - | awk '{for(i=1;i<=NF;i++){if(\$i ~ /MemoryCurrent=/){split(\$i,a,\"=\"); v=a[2]/1024/1024; if(v>0) printf \"  %.0f MB  \", v}}}'; echo"
ps -eo rss,comm --sort=-rss | head -6 | awk '{printf "  %6.0f MB  %s\n", $1/1024, $2}'

echo
echo "===== 8. 磁盘 ====="
df -h / | tail -1
echo "-- /opt/bp-platform --"
du -sh /opt/bp-platform 2>/dev/null

echo
echo "===== 9. 数据落库确认 ====="
echo "（通过应用创建的测试数据由外部脚本另行核查）"
