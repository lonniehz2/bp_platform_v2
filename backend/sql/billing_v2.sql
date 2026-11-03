-- 账单计费口径升级（MySQL 8）
-- 目的：自然月账单、按天折算、费用确认日、付款到期日、价格快照
ALTER TABLE bp_fin_bill
    ADD COLUMN settlement_date DATE NULL COMMENT '费用确认日（金额最终确定日，不含付款含义）' AFTER period_end,
    ADD COLUMN unit_price_snapshot DECIMAL(14,4) NULL COMMENT '本次计费实际使用的单价快照' AFTER bill_amount,
    ADD COLUMN price_source VARCHAR(20) NULL COMMENT 'CONTRACT_RENT / FEE_ITEM' AFTER unit_price_snapshot,
    ADD COLUMN bill_date DATE NULL COMMENT '账单生成日（业务日期）' AFTER due_date,
    ADD COLUMN billing_days INT NULL COMMENT '计费天数（含首尾）' AFTER billing_quantity,
    ADD COLUMN proration_months DECIMAL(10,6) NULL COMMENT '折算月数' AFTER billing_days;

CREATE INDEX idx_bill_contract_period ON bp_fin_bill (contract_id, bill_period);
