import io
p=r'src\main\java\com\yundao\platform\service\WorkflowService.java'
s=io.open(p,encoding='utf-8').read()
if 'findFlowId' not in s:
 s=s.replace('''    public Map<String, Object> submit(long flowId, SubmitCmd cmd) {''','''    public long findFlowId(String sceneCode, String bizType) {
        List<Map<String, Object>> rows = jdbc.queryForList(
                "select id from bp_wf_flow where tenant_id=? and scene_code=? and biz_type=? "
                        + "and flow_status='ENABLED' and is_deleted=0 order by id desc limit 1",
                TenantContext.require(), sceneCode, bizType);
        if (rows.isEmpty()) {
            throw BizException.param("未配置审批流程");
        }
        return ((Number) rows.get(0).get("id")).longValue();
    }

    public Map<String, Object> submit(long flowId, SubmitCmd cmd) {''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('findFlowId added')
