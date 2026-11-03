-- 设备/表计水电预存
CREATE TABLE IF NOT EXISTS bp_fin_device_prepay_account (
    id BIGINT UNSIGNED PRIMARY KEY,
    tenant_id VARCHAR(32) NOT NULL,
    meter_point_id BIGINT UNSIGNED NOT NULL,
    contract_id BIGINT UNSIGNED NULL,
    space_id BIGINT UNSIGNED NULL,
    device_id VARCHAR(64) NULL,
    balance_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_in DECIMAL(14,2) NOT NULL DEFAULT 0,
    total_out DECIMAL(14,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    create_time DATETIME(3) NULL,
    update_time DATETIME(3) NULL,
    UNIQUE KEY uk_device_prepay_point (tenant_id, meter_point_id)
);

CREATE TABLE IF NOT EXISTS bp_fin_device_prepay_flow (
    id BIGINT UNSIGNED PRIMARY KEY,
    tenant_id VARCHAR(32) NOT NULL,
    account_id BIGINT UNSIGNED NOT NULL,
    meter_point_id BIGINT UNSIGNED NOT NULL,
    contract_id BIGINT UNSIGNED NULL,
    flow_type VARCHAR(20) NOT NULL,
    amount DECIMAL(14,2) NOT NULL,
    balance_after DECIMAL(14,2) NOT NULL,
    reading_value DECIMAL(14,4) NULL,
    usage_amount DECIMAL(14,4) NULL,
    biz_type VARCHAR(30) NULL,
    biz_id BIGINT UNSIGNED NULL,
    fee_amount DECIMAL(14,2) NULL,
    actual_amount DECIMAL(14,2) NULL,
    remark VARCHAR(500) NULL,
    create_time DATETIME(3) NULL
);

CREATE INDEX idx_device_prepay_flow_point ON bp_fin_device_prepay_flow (meter_point_id, create_time);
