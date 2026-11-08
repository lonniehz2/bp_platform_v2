-- 智慧物业 V1 客服/管家角色与权限
insert ignore into bp_iam_role
(id, tenant_id, role_code, role_name, role_type, data_scope, sort_no, status, remark, is_deleted, create_time, update_time)
values
(800000000000002001, '350600', 'PROPERTY_STEWARD', '物业客服/管家', 'CUSTOM', 'ORG_SUB',
 20, 'ENABLED', '物业项目客服/管家，项目内业务办理，不含财务配置与退款审批', 0, now(), now());

insert ignore into bp_iam_permission
(id, parent_id, perm_code, perm_name, perm_type, route_path, component, icon, scenario, sort_no, status, create_time)
values
(800000000000001001, null, 'property:project:view', '物业项目-查看', 'BUTTON', null, null, null, 'PROPERTY', 1, 'ENABLED', now()),
(800000000000001002, null, 'property:category:view', '物业分类-查看', 'BUTTON', null, null, null, 'PROPERTY', 2, 'ENABLED', now()),
(800000000000001003, null, 'property:unit:view', '物业房屋-查看', 'BUTTON', null, null, null, 'PROPERTY', 3, 'ENABLED', now()),
(800000000000001004, null, 'property:unit:edit', '物业房屋-编辑', 'BUTTON', null, null, null, 'PROPERTY', 4, 'ENABLED', now()),
(800000000000001005, null, 'property:owner:view', '业主关系-查看', 'BUTTON', null, null, null, 'PROPERTY', 5, 'ENABLED', now()),
(800000000000001006, null, 'property:owner:edit', '业主关系-编辑', 'BUTTON', null, null, null, 'PROPERTY', 6, 'ENABLED', now()),
(800000000000001007, null, 'property:bill:view', '物业账单-查看', 'BUTTON', null, null, null, 'PROPERTY', 7, 'ENABLED', now()),
(800000000000001008, null, 'property:bill:manage', '物业账单-办理', 'BUTTON', null, null, null, 'PROPERTY', 8, 'ENABLED', now()),
(800000000000001009, null, 'property:payment:create', '物业收款-办理', 'BUTTON', null, null, null, 'PROPERTY', 9, 'ENABLED', now()),
(800000000000001010, null, 'property:receipt:view', '物业收据-查看', 'BUTTON', null, null, null, 'PROPERTY', 10, 'ENABLED', now()),
(800000000000001011, null, 'property:parking:view', '车位-查看', 'BUTTON', null, null, null, 'PROPERTY', 11, 'ENABLED', now()),
(800000000000001012, null, 'property:parking:manage', '车位-办理', 'BUTTON', null, null, null, 'PROPERTY', 12, 'ENABLED', now()),
(800000000000001013, null, 'property:meter:view', '水电抄表-查看', 'BUTTON', null, null, null, 'PROPERTY', 13, 'ENABLED', now()),
(800000000000001014, null, 'property:meter:manage', '水电抄表-办理', 'BUTTON', null, null, null, 'PROPERTY', 14, 'ENABLED', now()),
(800000000000001015, null, 'property:dunning:view', '欠费催缴-查看', 'BUTTON', null, null, null, 'PROPERTY', 15, 'ENABLED', now()),
(800000000000001016, null, 'property:dunning:create', '欠费催缴-发起', 'BUTTON', null, null, null, 'PROPERTY', 16, 'ENABLED', now()),
(800000000000001017, null, 'property:invoice:view', '电子发票-查看', 'BUTTON', null, null, null, 'PROPERTY', 17, 'ENABLED', now()),
(800000000000001018, null, 'property:invoice:request', '电子发票-申请', 'BUTTON', null, null, null, 'PROPERTY', 18, 'ENABLED', now()),
(800000000000001019, null, 'property:expense:view', '物业支出-查看', 'BUTTON', null, null, null, 'PROPERTY', 19, 'ENABLED', now()),
(800000000000001020, null, 'property:report:view', '经营报表-查看', 'BUTTON', null, null, null, 'PROPERTY', 20, 'ENABLED', now());

insert ignore into bp_iam_role_permission(id, tenant_id, role_id, permission_id, create_time)
select 800000000000003000 + row_number() over (order by id), '350600', 800000000000002001, id, now()
from bp_iam_permission
where perm_code in (
 'property:project:view','property:category:view','property:unit:view','property:unit:edit',
 'property:owner:view','property:owner:edit','property:bill:view','property:bill:manage',
 'property:payment:create','property:receipt:view','property:parking:view','property:parking:manage',
 'property:meter:view','property:meter:manage','property:dunning:view','property:dunning:create',
 'property:invoice:view','property:invoice:request','property:expense:view','property:report:view'
);
