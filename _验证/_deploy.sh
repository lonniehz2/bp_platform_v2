set -e
echo hzbit56771010 | sudo -S systemctl stop bp-platform
sleep 2
echo hzbit56771010 | sudo -S mv /tmp/bp-platform.jar /opt/bp-platform/bp-platform.jar
echo hzbit56771010 | sudo -S chown bp:bp /opt/bp-platform/bp-platform.jar
echo hzbit56771010 | sudo -S systemctl start bp-platform
sleep 8
systemctl is-active bp-platform
