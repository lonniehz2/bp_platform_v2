-- 合同预收余额
CREATE TABLE IF NOT EXISTS bp_fin_prepay_account (
    id BIGINT UNSIGNED PRIMARY KEY,
    tenant_id VARCHAR(32) NOT NULL,
    contract_id BIGINT UNSIGNED NOT NULL,
    person_id BIGINT UNSIGNED NULL,
    org_id BIGINT UNSIGNED NULL,
    balance_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_in DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_out DECIMAL(14,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    create_time DATETIME(3) NULL,
    update_time DATETIME(3) NULL,
    UNIQUE KEY uk_prepay_contract (tenant_id, contract_id)
);

CREATE TABLE IF NOT EXISTS bp_fin_prepay_flow (
    id BIGINT UNSIGNED PRIMARY KEY,
    tenant_id VARCHAR(32) NOT NULL,
    account_id BIGINT UNSIGNED NOT NULL,
    contract_id BIGINT UNSIGNED NOT NULL,
    flow_type VARCHAR(20) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    balance_after DECIMAL(14,2) NOT NULL,
    biz_type VARCHAR(30) NULL,
    biz_id BIGINT UNSIGNED NULL,
    pay_channel VARCHAR(20) NULL,
    trade_no VARCHAR(64) NULL,
    fee_amount DECIMAL(14,2) NULL,
    actual_amount DECIMAL(14,2) NULL,
    remark VARCHAR(500) NULL,
    create_time DATETIME(3) NULL
);

CREATE INDEX idx_prepay_flow_contract ON bp_fin_prepay_flow (contract_id, create_time);
