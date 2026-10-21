ROOTPW='hzbit56771010'
export LANG=C LC_ALL=C

echo "===== 1. 确认可用版本（LANG=C）====="
for p in openjdk-21-jdk-headless redis-server rabbitmq-server; do
  c=$(apt-cache policy $p 2>/dev/null | awk '/Candidate/{print $2}')
  printf "  %-32s %s\n" "$p" "${c:-不可用}"
done

echo
echo "===== 2. 安装 Java 21 + Redis + RabbitMQ ====="
echo "$ROOTPW" | su - root -c "
export DEBIAN_FRONTEND=noninteractive LANG=C LC_ALL=C
apt-get install -y --no-install-recommends \
  openjdk-21-jdk-headless redis-server rabbitmq-server 2>&1 | tail -30
"

echo
echo "===== 3. 验证 ====="
echo "-- Java --"
java -version 2>&1 | head -3
echo "-- Redis --"
redis-server --version 2>&1 | head -1
echo "-- RabbitMQ --"
echo "$ROOTPW" | su - root -c "rabbitmqctl version 2>&1 | head -2"

echo
echo "===== 4. 服务状态 ====="
systemctl is-enabled redis-server rabbitmq-server 2>&1
systemctl is-active redis-server rabbitmq-server 2>&1
