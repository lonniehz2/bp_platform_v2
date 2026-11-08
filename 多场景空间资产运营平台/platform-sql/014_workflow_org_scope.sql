-- 审批流程组织级覆盖（已有库升级用）

alter table bp_wf_flow
  add column org_id bigint null comment '组织ID，空表示场景默认流程' after biz_type;

create index idx_wf_flow_org on bp_wf_flow (tenant_id, scene_code, biz_type, org_id);
