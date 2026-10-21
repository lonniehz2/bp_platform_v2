set -e
ROOTPW='hzbit56771010'

echo "===== 安装基础工具（curl / git / pip / venv / 编译工具）====="
echo "$ROOTPW" | su - root -c "
export DEBIAN_FRONTEND=noninteractive
apt-get install -y --no-install-recommends \
  curl git ca-certificates \
  python3-pip python3-venv python3-dev \
  build-essential pkg-config \
  htop tree jq net-tools lsof unzip \
  libopenblas-dev libgomp1 2>&1 | tail -15
"

echo
echo "===== 配置 pip 国内镜像（全局，避免每次 -i）====="
echo "$ROOTPW" | su - root -c "mkdir -p /etc/pip && cat > /etc/pip.conf <<'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 60
EOF
echo '  pip.conf 已写入 /etc/pip.conf'"

echo
echo "===== 验证工具链 ====="
for c in curl git python3 pip3 gcc make htop jq; do
  v=$(command -v $c 2>/dev/null)
  if [ -n "$v" ]; then
    ver=$($c --version 2>&1 | head -1 | cut -c1-60)
    printf "  %-10s %s\n" "$c" "$ver"
  else
    printf "  %-10s 未安装\n" "$c"
  fi
done

echo
echo "===== 验证 PyPI（走全局镜像）====="
pip3 config list 2>/dev/null || echo "  (pip3 config 无输出)"
python3 -m pip --version 2>&1 | head -1
