#!/usr/bin/env python3
"""保障房老库 -> 多场景平台新库迁移脚本（dry-run 默认）。

用法：
  python migrate_legacy.py
  python migrate_legacy.py --apply

环境变量：
  OLD_DB_HOST / OLD_DB_PORT / OLD_DB_USER / OLD_DB_PASSWORD / OLD_DB_NAME
  NEW_DB_HOST / NEW_DB_PORT / NEW_DB_USER / NEW_DB_PASSWORD / NEW_DB_NAME
"""

import argparse
import hashlib
import os
import sys

import pymysql


def env(name, default):
    return os.environ.get(name, default)


OLD = {
    "host": env("OLD_DB_HOST", "192.168.31.153"),
    "port": int(env("OLD_DB_PORT", "33306")),
    "user": env("OLD_DB_USER", "root"),
    "password": env("OLD_DB_PASSWORD", env("DB_PASSWORD", "")),
    "database": env("OLD_DB_NAME", "bp_platform"),
}
NEW = {
    "host": env("NEW_DB_HOST", "192.168.31.153"),
    "port": int(env("NEW_DB_PORT", "33306")),
    "user": env("NEW_DB_USER", "root"),
    "password": env("NEW_DB_PASSWORD", env("DB_PASSWORD", "")),
    "database": env("NEW_DB_NAME", "bp_platform_v2"),
}

TENANT = "350600"


def connect(cfg):
    return pymysql.connect(
        host=cfg["host"], port=cfg["port"], user=cfg["user"],
        password=cfg["password"], database=cfg["database"],
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def scalar(cur, sql, args=()):
    cur.execute(sql, args)
    row = cur.fetchone()
    return list(row.values())[0] if row else None


def count_table(cur, table):
    return scalar(cur, f"select count(*) from {table}")


def migrate(apply=False):
    old = connect(OLD)
    new = connect(NEW)
    oc, nc = old.cursor(), new.cursor()

    template_id = scalar(nc,
        "select id from bp_space_template where tenant_id=%s and template_code='GUARANTEE_BASE' limit 1",
        (TENANT,))
    if not template_id:
        raise RuntimeError("新库缺少 GUARANTEE_BASE 模板")

    stats = {}
    inserted = {k: 0 for k in ("org", "space", "house", "person", "contract", "bill", "grant", "device",
                              "application", "waitlist", "allocation", "payment", "payment_allocation", "receipt",
                              "deposit", "subsidy", "subsidy_standard", "contract_change", "role", "user", "user_role",
                              "role_menu")}
    try:
        # 1. 组织/项目
        oc.execute("""
            select id, tenant_id, parent_id, org_code, org_name, org_type, org_path,
                   sort_no, status, is_deleted
            from bp_iam_org
            order by id
        """)
        orgs = oc.fetchall()
        stats["org"] = len(orgs)
        for r in orgs:
            if apply:
                nc.execute("""
                    insert ignore into bp_org
                      (id, tenant_id, parent_id, org_code, org_name, org_type, scene_code,
                       business_mode, space_template_id, org_path, sort_no, status, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,'GUARANTEE','PUBLIC_RENTAL',%s,%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["parent_id"], r["org_code"], r["org_name"],
                      r["org_type"], template_id, r["org_path"], r["sort_no"],
                      r["status"], r["is_deleted"]))
                inserted["org"] += nc.rowcount

        # 2. 空间
        oc.execute("""
            select id, tenant_id, org_id, parent_id, space_code, space_name, space_type,
                   space_path, space_level, area, sort_no, status, is_deleted
            from bp_asset_space order by space_level, id
        """)
        spaces = oc.fetchall()
        stats["space"] = len(spaces)
        for r in spaces:
            asset_type = "BED" if r["space_type"] == "BED" else "PUBLIC_RENTAL"
            if apply:
                nc.execute("""
                    insert ignore into bp_space
                      (id, tenant_id, org_id, parent_id, space_code, space_name, space_type,
                       space_path, level_no, asset_type_code, space_template_id, business_mode,
                       sub_unit_mode, area, sort_no, status, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PUBLIC_RENTAL',null,%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["org_id"], r["parent_id"], r["space_code"],
                      r["space_name"], r["space_type"], r["space_path"], r["space_level"],
                      asset_type, template_id, r["area"], r["sort_no"], r["status"], r["is_deleted"]))
                inserted["space"] += nc.rowcount

        # 3. 房屋
        oc.execute("""
            select id, tenant_id, org_id, space_id, house_code, house_name, area, inner_area,
                   house_status, is_deleted
            from bp_asset_house order by id
        """)
        houses = oc.fetchall()
        stats["house"] = len(houses)
        for r in houses:
            status = {"PENDING_ALLOC": "VACANT", "VACANT": "VACANT",
                      "ALLOCATED": "ALLOCATED"}.get(r["house_status"], r["house_status"] or "VACANT")
            if apply and r["space_id"]:
                nc.execute("""
                    insert ignore into bp_house
                      (id, tenant_id, org_id, space_id, house_code, house_name, asset_type_code,
                       area, inner_area, house_status, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,'PUBLIC_RENTAL',%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["org_id"], r["space_id"], r["house_code"],
                      r["house_name"], r["area"], r["inner_area"], status, r["is_deleted"]))
                inserted["house"] += nc.rowcount

        # 4. 人员
        oc.execute("""
            select id, tenant_id, person_code, person_name, phone, id_card_mask,
                   person_source, verify_status, person_status, is_deleted
            from bp_person order by id
        """)
        persons = oc.fetchall()
        stats["person"] = len(persons)
        for r in persons:
            if apply:
                nc.execute("""
                    insert ignore into bp_person
                      (id, tenant_id, person_code, person_name, phone, id_card_mask,
                       person_type, verify_status, status, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["person_code"], r["person_name"], r["phone"],
                      r["id_card_mask"], r["person_source"], r["verify_status"],
                      r["person_status"] or "ENABLED", r["is_deleted"]))
                inserted["person"] += nc.rowcount

        # 5. 合同
        oc.execute("""
            select id, tenant_id, org_id, contract_no, lessee_person_id, house_id,
                   lease_start, lease_end, monthly_rent, deposit_amount, pay_cycle, pay_day,
                   contract_status, is_deleted
            from bp_biz_contract order by id
        """)
        contracts = oc.fetchall()
        stats["contract"] = len(contracts)
        for r in contracts:
            status = {"EFFECTIVE": "ACTIVE", "ACTIVE": "ACTIVE",
                      "PENDING": "PENDING", "TERMINATED": "TERMINATED"}.get(
                          r["contract_status"], r["contract_status"] or "ACTIVE")
            if apply and r["house_id"] and r["lessee_person_id"]:
                nc.execute("""
                    insert ignore into guarantee_contract
                      (id, tenant_id, project_id, contract_no, house_id, person_id,
                       start_date, end_date, rent_amount, deposit_amount, billing_cycle,
                       bill_day, contract_status, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["org_id"], r["contract_no"], r["house_id"],
                      r["lessee_person_id"], r["lease_start"], r["lease_end"],
                      r["monthly_rent"], r["deposit_amount"], r["pay_cycle"], r["pay_day"],
                      status, r["is_deleted"]))
                inserted["contract"] += nc.rowcount

        # 6. 账单
        oc.execute("""
            select id, tenant_id, org_id, bill_no, contract_id, house_id, person_id,
                   period_start, period_end, bill_amount, discount_amount, paid_amount,
                   payable_amount, bill_status, due_date, is_deleted
            from bp_fin_bill order by id
        """)
        bills = oc.fetchall()
        stats["bill"] = len(bills)
        for r in bills:
            if apply:
                nc.execute("""
                    insert ignore into bp_bill
                      (id, tenant_id, project_id, bill_no, biz_type, contract_type, contract_id,
                       house_id, person_id, fee_item_code, period_start, period_end, amount,
                       discount_amount, payable_amount, paid_amount, bill_status, due_date,
                       source_type, source_id, is_deleted)
                    values (%s,%s,%s,%s,'GUARANTEE_RENT','GUARANTEE_CONTRACT',%s,%s,%s,
                            'GUARANTEE_RENT',%s,%s,%s,%s,%s,%s,%s,%s,'LEGACY',%s,%s)
                """, (r["id"], r["tenant_id"], r["org_id"], r["bill_no"], r["contract_id"],
                      r["house_id"], r["person_id"], r["period_start"], r["period_end"],
                      r["bill_amount"], r["discount_amount"], r["payable_amount"],
                      r["paid_amount"], r["bill_status"], r["due_date"], r["id"], r["is_deleted"]))
                inserted["bill"] += nc.rowcount
                if nc.rowcount == 0:
                    nc.execute("select count(*) from bp_bill where id=%s", (r["id"],))
                    if nc.fetchone()["count(*)"] == 0:
                        payload = (f"bill_no={r['bill_no']};contract_id={r['contract_id']};"
                                   f"period={r['period_start']}~{r['period_end']}")
                        ex_id = int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:15], 16)
                        nc.execute("""
                            insert ignore into bp_migration_exception
                              (id, source_table, source_id, reason, payload)
                            values (%s,'bp_fin_bill',%s,'账单合同周期重复或主键冲突',%s)
                        """, (ex_id, r["id"], payload))

        # 7. 申请
        oc.execute("""
            select id, tenant_id, org_id, application_no, person_id, security_type,
                   family_size, application_status, apply_time, accept_time, reject_reason, is_deleted
            from bp_biz_application order by id
        """)
        applications = oc.fetchall()
        stats["application"] = len(applications)
        for r in applications:
            status = {"REVIEWING": "SUBMITTED", "APPROVED": "APPROVED",
                      "REJECTED": "REJECTED", "DRAFT": "DRAFT"}.get(
                          r["application_status"], r["application_status"] or "DRAFT")
            if apply:
                nc.execute("""
                    insert ignore into guarantee_application
                      (id, tenant_id, project_id, application_no, applicant_person_id,
                       application_type, family_size, application_status, submit_time,
                       review_time, review_comment, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["org_id"], r["application_no"], r["person_id"],
                      r["security_type"] or "PUBLIC_RENTAL", r["family_size"] or 1,
                      status, r["apply_time"], r["accept_time"],
                      r["reject_reason"], r["is_deleted"]))
                inserted["application"] += nc.rowcount

        # 8. 轮候
        oc.execute("""
            select id, tenant_id, org_id, application_id, waiting_no, queue_status,
                   enter_time
            from bp_biz_waiting_queue order by id
        """)
        waitlist = oc.fetchall()
        stats["waitlist"] = len(waitlist)
        for r in waitlist:
            if apply:
                nc.execute("""
                    insert ignore into guarantee_waitlist
                      (id, tenant_id, project_id, application_id, queue_no, waitlist_status,
                       joined_time, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,0)
                """, (r["id"], r["tenant_id"], r["org_id"], r["application_id"],
                      r["waiting_no"], r["queue_status"] or "WAITING",
                      r["enter_time"]))
                inserted["waitlist"] += nc.rowcount

        # 9. 配租
        oc.execute("""
            select id, tenant_id, allocation_no, person_id, house_id, allocation_date,
                   allocation_status
            from bp_biz_allocation order by id
        """)
        allocations = oc.fetchall()
        stats["allocation"] = len(allocations)
        for r in allocations:
            if apply:
                nc.execute("""
                    insert ignore into guarantee_application
                      (id, tenant_id, project_id, application_no, applicant_person_id,
                       application_type, family_size, application_status, submit_time,
                       review_time, review_comment, is_deleted)
                    values (%s,%s,%s,%s,%s,'LEGACY',1,'APPROVED',%s,%s,'历史配租导入',0)
                """, (r["id"], r["tenant_id"], r["tenant_id"], "LEGACY-ALLOC-" + str(r["allocation_no"]),
                      r["person_id"], r["allocation_date"], r["allocation_date"]))
                status = "ALLOCATED" if r["allocation_status"] in ("LOCKED", "CONFIRMED") else "CANCELLED"
                nc.execute("""
                    insert ignore into guarantee_allocation
                      (id, tenant_id, project_id, application_id, house_id, allocation_no,
                       allocation_status, allocated_time, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,0)
                """, (r["id"], r["tenant_id"], r["tenant_id"], r["id"], r["house_id"],
                      r["allocation_no"], status, r["allocation_date"]))
                if nc.rowcount > 0:
                    inserted["allocation"] += 1
                    if status == "ALLOCATED":
                        nc.execute("update bp_house set house_status='ALLOCATED' where id=%s", (r["house_id"],))

        # 10. 支付
        oc.execute("""
            select id, tenant_id, org_id, payment_no, person_id, pay_amount, pay_channel,
                   pay_status, pay_time, remark
            from bp_fin_payment order by id
        """)
        payments = oc.fetchall()
        stats["payment"] = len(payments)
        for r in payments:
            if apply:
                nc.execute("""
                    insert ignore into bp_payment
                      (id, tenant_id, project_id, payment_no, payer_person_id, amount,
                       payment_method, payment_status, paid_time, remark, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                """, (r["id"], r["tenant_id"], r["org_id"], r["payment_no"], r["person_id"],
                      r["pay_amount"], r["pay_channel"] or "CASH", r["pay_status"] or "SUCCESS",
                      r["pay_time"], r["remark"]))
                inserted["payment"] += nc.rowcount

        # 10. 支付分摊
        oc.execute("""
            select id, tenant_id, payment_id, bill_id, allocate_amount
            from bp_fin_payment_allocate order by id
        """)
        payment_allocations = oc.fetchall()
        stats["payment_allocation"] = len(payment_allocations)
        for r in payment_allocations:
            if apply:
                nc.execute("""
                    insert ignore into bp_payment_allocation
                      (id, tenant_id, payment_id, bill_id, amount)
                    values (%s,%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["payment_id"], r["bill_id"], r["allocate_amount"]))
                inserted["payment_allocation"] += nc.rowcount

        # 11. 收据
        oc.execute("""
            select id, tenant_id, project_id, receipt_no, payment_id, amount,
                   receipt_status, issued_at
            from prop_receipt order by id
        """)
        receipts = oc.fetchall()
        stats["receipt"] = len(receipts)
        for r in receipts:
            if apply:
                nc.execute("""
                    insert ignore into bp_receipt
                      (id, tenant_id, project_id, receipt_no, payment_id, amount,
                       receipt_status, issued_time, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,0)
                """, (r["id"], r["tenant_id"], r["project_id"], r["receipt_no"], r["payment_id"],
                      r["amount"], r["receipt_status"] or "ISSUED", r["issued_at"]))
                inserted["receipt"] += nc.rowcount

        # 12. 押金
        oc.execute("""
            select id, tenant_id, org_id, contract_id, person_id, deposit_amount,
                   paid_amount, deduct_amount, refund_amount, deposit_status
            from bp_fin_deposit order by id
        """)
        deposits = oc.fetchall()
        stats["deposit"] = len(deposits)
        for r in deposits:
            if apply:
                nc.execute("""
                    insert ignore into guarantee_deposit
                      (id, tenant_id, project_id, contract_id, person_id, amount,
                       paid_amount, refunded_amount, deposit_status, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                """, (r["id"], r["tenant_id"], r["org_id"], r["contract_id"], r["person_id"],
                      r["deposit_amount"], r["paid_amount"], r["refund_amount"],
                      r["deposit_status"] or "PENDING"))
                inserted["deposit"] += nc.rowcount

        # 13. 补贴
        oc.execute("""
            select id, tenant_id, org_id, contract_id, subsidy_period, subsidy_amount,
                   record_status, record_no
            from bp_fin_subsidy_record order by id
        """)
        subsidies = oc.fetchall()
        stats["subsidy"] = len(subsidies)
        for r in subsidies:
            if apply:
                period = str(r["subsidy_period"] or "")
                start = f"{period[:4]}-{period[4:6]}-01" if len(period) >= 6 else None
                end = None
                if start:
                    import calendar
                    y, m = int(period[:4]), int(period[4:6])
                    end = f"{y:04d}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}"
                if start and end:
                    nc.execute("""
                        insert ignore into guarantee_subsidy
                          (id, tenant_id, project_id, contract_id, subsidy_type, subsidy_amount,
                           start_date, end_date, subsidy_status, remark, is_deleted)
                        values (%s,%s,%s,%s,'MIGRATED_SUBSIDY',%s,%s,%s,'ACTIVE',%s,0)
                    """, (r["id"], r["tenant_id"], r["org_id"], r["contract_id"],
                          r["subsidy_amount"], start, end, r["record_no"]))
                    inserted["subsidy"] += nc.rowcount

        # 14. 补贴标准
        oc.execute("""
            select id, tenant_id, org_id, standard_code, standard_name, security_type,
                   income_level, family_type, talent_level, subsidy_mode, subsidy_value,
                   max_amount, effective_start, effective_end, status, is_deleted
            from bp_fin_subsidy_standard order by id
        """)
        standards = oc.fetchall()
        stats["subsidy_standard"] = len(standards)
        for r in standards:
            if apply:
                nc.execute("""
                    insert ignore into guarantee_subsidy_standard
                      (id,tenant_id,project_id,standard_code,standard_name,security_type,
                       income_level,family_type,talent_level,subsidy_mode,subsidy_value,
                       max_amount,effective_start,effective_end,standard_status,is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["org_id"], r["standard_code"], r["standard_name"],
                      r["security_type"], r["income_level"], r["family_type"], r["talent_level"],
                      r["subsidy_mode"], r["subsidy_value"], r["max_amount"],
                      r["effective_start"], r["effective_end"], r["status"] or "ENABLED",
                      r["is_deleted"]))
                inserted["subsidy_standard"] += nc.rowcount

        # 15. 合同变更
        oc.execute("""
            select id, tenant_id, contract_id, change_type, change_reason, before_json,
                   after_json, approve_status, effective_date
            from bp_biz_contract_change order by id
        """)
        changes = oc.fetchall()
        stats["contract_change"] = len(changes)
        for r in changes:
            if apply:
                project_id = scalar(nc, "select project_id from guarantee_contract where id=%s",
                                    (r["contract_id"],))
                if project_id is None:
                    continue
                change_type = {"RENT_ADJUST": "RENT_CHANGE", "TERMINATE": "TERMINATION",
                               "ROOM_CHANGE": "ROOM_CHANGE", "TERM_CHANGE": "TERM_CHANGE"}.get(
                                   r["change_type"], r["change_type"])
                status = {"APPROVED": "APPROVED", "PENDING": "APPROVING",
                          "REJECTED": "REJECTED"}.get(r["approve_status"], "APPROVED")
                nc.execute("""
                    insert ignore into guarantee_contract_change
                      (id, tenant_id, project_id, contract_id, change_type, before_json,
                       after_json, effective_date, change_status, reason, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                """, (r["id"], r["tenant_id"], project_id, r["contract_id"], change_type,
                      r["before_json"], r["after_json"], r["effective_date"], status,
                      r["change_reason"]))
                inserted["contract_change"] += nc.rowcount

        # 15. 授权
        oc.execute("""
            select id, tenant_id, org_id, person_id, space_id, grant_level,
                   valid_start, valid_end, source_type, source_id, grant_status, is_deleted
            from bp_grant_entitlement where space_id is not null order by id
        """)
        grants = oc.fetchall()
        stats["grant"] = len(grants)
        for r in grants:
            if apply:
                nc.execute("""
                    insert ignore into bp_grant_entitlement
                      (id, tenant_id, project_id, person_id, target_type, target_id,
                       grant_level, valid_start, valid_end, grant_status, source_type,
                       source_id, is_deleted)
                    values (%s,%s,%s,%s,'SPACE',%s,%s,%s,%s,%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["org_id"], r["person_id"], r["space_id"],
                      r["grant_level"], r["valid_start"], r["valid_end"], r["grant_status"],
                      r["source_type"], r["source_id"], r["is_deleted"]))
                inserted["grant"] += nc.rowcount

        # 8. 设备
        oc.execute("""
            select id, tenant_id, org_id, space_id, device_id, device_name, device_type,
                   device_model, install_time, is_deleted
            from bp_dev_device order by id
        """)
        devices = oc.fetchall()
        stats["device"] = len(devices)
        for r in devices:
            if apply:
                nc.execute("""
                    insert ignore into bp_dev_device
                      (id, tenant_id, project_id, space_id, device_code, device_name,
                       device_type, device_model, asset_status, business_status,
                       install_time, is_deleted)
                    values (%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE','IN_USE',%s,%s)
                """, (r["id"], r["tenant_id"], r["org_id"], r["space_id"], r["device_id"],
                      r["device_name"], r["device_type"], r["device_model"],
                      r["install_time"], r["is_deleted"]))
                inserted["device"] += nc.rowcount

        # 16. 角色/用户
        oc.execute("""
            select id, tenant_id, role_code, role_name, role_type, status
            from bp_iam_role order by id
        """)
        roles = oc.fetchall()
        stats["role"] = len(roles)
        role_map = {}
        for r in roles:
            existing = scalar(nc, "select id from bp_role where tenant_id=%s and scene_code='GUARANTEE' "
                                  "and role_code=%s", (r["tenant_id"], r["role_code"]))
            if existing:
                role_map[r["id"]] = existing
                continue
            role_map[r["id"]] = r["id"]
            if apply:
                nc.execute("""
                    insert ignore into bp_role(id,tenant_id,scene_code,role_code,role_name,role_status)
                    values (%s,%s,'GUARANTEE',%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["role_code"], r["role_name"], r["status"] or "ENABLED"))
                inserted["role"] += nc.rowcount

        oc.execute("""
            select id, tenant_id, username, password_hash, real_name, status
            from bp_iam_user order by id
        """)
        users = oc.fetchall()
        stats["user"] = len(users)
        for r in users:
            if apply:
                nc.execute("""
                    insert ignore into bp_user
                      (id,tenant_id,username,password_hash,display_name,user_status,is_deleted)
                    values (%s,%s,%s,%s,%s,%s,0)
                """, (r["id"], r["tenant_id"], r["username"], r["password_hash"],
                      r["real_name"] or r["username"], r["status"] or "ENABLED"))
                inserted["user"] += nc.rowcount

        oc.execute("select id, tenant_id, user_id, role_id from bp_iam_user_role order by id")
        user_roles = oc.fetchall()
        stats["user_role"] = len(user_roles)
        for r in user_roles:
            if apply and r["role_id"] in role_map:
                nc.execute("""
                    insert ignore into bp_user_role(id,tenant_id,user_id,role_id)
                    values (%s,%s,%s,%s)
                """, (r["id"], r["tenant_id"], r["user_id"], role_map[r["role_id"]]))
                inserted["user_role"] += nc.rowcount

        # 17. 旧角色页面权限 -> 新场景菜单
        path_menu = {
            "/dashboard": "dashboard",
            "/applications": "application",
            "/allocations": "application",
            "/waitlist": "waitlist",
            "/persons": "person",
            "/contracts": "contract",
            "/contract-changes": "contract",
            "/exchanges": "contract",
            "/terminations": "contract",
            "/annual-reviews": "contract",
            "/bills": "billing",
            "/deposits": "billing",
            "/subsidies": "billing",
            "/arrears": "billing",
            "/cashflow": "billing",
            "/fee-items": "billing",
            "/devices": "device",
            "/grants": "device",
            "/keyring": "device",
            "/access": "device",
            "/spaces": "asset",
            "/houses": "asset",
            "/orgs": "config",
            "/rbac": "config",
            "/sys": "system",
            "/reports": "system",
            "/publicities": "application",
            "/workorders": "service",
            "/access": "access",
            "/complaints": "complaint",
            "/appeals": "complaint",
            "/visits": "complaint",
        }
        oc.execute("""
            select r.id role_id, p.route_path route_path
            from bp_iam_role r
            join bp_iam_role_permission rp on rp.role_id=r.id
            join bp_iam_permission p on p.id=rp.permission_id
            where p.perm_code like 'page:%' and p.route_path is not null
        """)
        page_perms = oc.fetchall()
        stats["role_menu"] = len(page_perms)
        for r in page_perms:
            menu_code = path_menu.get(r["route_path"])
            if not menu_code:
                continue
            menu_id = scalar(nc, "select id from bp_menu where scene_code='GUARANTEE' and menu_code=%s",
                             (menu_code,))
            if not menu_id:
                continue
            new_role_id = role_map.get(r["role_id"])
            if not new_role_id:
                continue
            ex_id = int(hashlib.sha256(f"role-menu-{new_role_id}-{menu_id}".encode("utf-8")).hexdigest()[:15], 16)
            if apply:
                nc.execute("""
                    insert ignore into bp_role_menu(id,tenant_id,role_id,menu_id)
                    values (%s,%s,%s,%s)
                """, (ex_id, TENANT, new_role_id, menu_id))
                inserted["role_menu"] += nc.rowcount

        if apply:
            new.commit()
        print("\n" + ("MIGRATED" if apply else "DRY-RUN") + " 旧库 -> 新库")
        for k, v in stats.items():
            if apply:
                print(f"  {k}: source={v} inserted={inserted[k]} skipped={v - inserted[k]}")
            else:
                print(f"  {k}: {v}")
        print("\n新库当前行数：")
        for table in ("bp_org", "bp_space", "bp_house", "bp_person",
                      "guarantee_contract", "bp_bill", "bp_grant_entitlement", "bp_dev_device"):
            print(f"  {table}: {count_table(nc, table)}")
    except Exception:
        new.rollback()
        raise
    finally:
        old.close()
        new.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="实际写入新库；默认只统计")
    args = parser.parse_args()
    try:
        migrate(apply=args.apply)
    except Exception as e:
        print("MIGRATION FAILED:", e, file=sys.stderr)
        sys.exit(1)
