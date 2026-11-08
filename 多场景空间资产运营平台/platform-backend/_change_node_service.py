import io
p=r'src\main\java\com\yundao\platform\service\GuaranteeContractChangeService.java'
s=io.open(p,encoding='utf-8').read()
old='''        return jdbc.queryForList(
                "select id, contract_id contractId, change_type changeType, effective_date effectiveDate, "
                        + "change_status changeStatus, reason, workflow_task_id workflowTaskId, "
                        + "before_json beforeJson, after_json afterJson, create_time createTime "
                        + "from guarantee_contract_change where tenant_id=? and contract_id=? and is_deleted=0 "
                        + "order by id desc",
                TenantContext.require(), contractId);'''
new='''        return jdbc.queryForList(
                "select c.id, c.contract_id contractId, c.change_type changeType, c.effective_date effectiveDate, "
                        + "c.change_status changeStatus, c.reason, c.workflow_task_id workflowTaskId, "
                        + "c.before_json beforeJson, c.after_json afterJson, c.create_time createTime, "
                        + "n.node_name currentNode "
                        + "from guarantee_contract_change c "
                        + "left join bp_wf_task t on t.id=c.workflow_task_id "
                        + "left join bp_wf_node n on n.id=t.current_node_id "
                        + "where c.tenant_id=? and c.contract_id=? and c.is_deleted=0 "
                        + "order by c.id desc",
                TenantContext.require(), contractId);'''
if old not in s: raise SystemExit('sql marker missing')
s=s.replace(old,new,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('current node backend')
