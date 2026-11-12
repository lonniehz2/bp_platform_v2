#!/usr/bin/env python3
"""只对 8090 的远程数据库执行 023-027 迁移。必须先跑 backup-8090.sh。"""
import os, sys
from pathlib import Path
import pymysql
from pymysql.constants import CLIENT

BASE = Path(__file__).resolve().parents[2] / "platform-sql"
FILES = ["023_menu_reorg.sql", "024_menu_label_fix.sql", "025_scene_menus_roles.sql", "026_scene_roles_cleanup.sql", "027_cleanup_verify_projects.sql"]

host = os.environ.get("DB_HOST", "192.168.31.153")
port = int(os.environ.get("DB_PORT", "33306"))
user = os.environ.get("DB_USER", "root")
password = os.environ.get("DB_PASSWORD")
database = os.environ.get("DB_NAME", "bp_platform_v2")
if not password:
    raise SystemExit("DB_PASSWORD is required")
if input(f"Apply 023-027 to {host}:{port}/{database}? type MIGRATE: ") != "MIGRATE":
    raise SystemExit("aborted")

conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database,
                       charset="utf8mb4", autocommit=False, client_flag=CLIENT.MULTI_STATEMENTS)
try:
    with conn.cursor() as cur:
        for name in FILES:
            path = BASE / name
            sql = path.read_text(encoding="utf-8")
            print("apply", name)
            cur.execute(sql)
            while cur.nextset():
                pass
    conn.commit()
    print("migration ok")
finally:
    conn.close()
