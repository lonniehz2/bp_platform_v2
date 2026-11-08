import io
p='backup-db.sh'
s=io.open(p,encoding='utf-8').read()
old='''mysqldump \\
  --single-transaction \\
  --routines \\
  --triggers \\
  --set-gtid-purged=OFF \\
  -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" \\
  "$DB_NAME" | gzip > "$OUT"

test -s "$OUT"'''
new='''if command -v mysqldump >/dev/null 2>&1; then
  mysqldump \\
    --single-transaction \\
    --routines \\
    --triggers \\
    --set-gtid-purged=OFF \\
    -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" \\
    "$DB_NAME" | gzip > "$OUT"
else
  # 无 mysqldump 时使用 JDBC 逻辑备份工具
  BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
  DRIVER="$BASE_DIR/mysql-connector-j-8.3.0.jar"
  if [ ! -f "$DRIVER" ] || [ ! -f "$BASE_DIR/DbBackup.class" ]; then
    echo "mysqldump missing and JDBC backup tool not assembled" >&2
    exit 3
  fi
  RAW="${OUT%.gz}"
  java -cp "$DRIVER:$BASE_DIR" DbBackup \\
    "$DB_HOST" "$DB_PORT" "$DB_USER" "$DB_PASSWORD" "$DB_NAME" "$RAW"
  gzip -f "$RAW"
fi

test -s "$OUT"'''
if old not in s: raise SystemExit('old missing')
s=s.replace(old,new,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('backup fallback')
