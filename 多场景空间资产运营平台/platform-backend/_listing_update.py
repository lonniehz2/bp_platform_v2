import io
p=r'src\main\java\com\yundao\platform\service\ListingService.java'
s=io.open(p,encoding='utf-8').read()
insert='''
    public Map<String, Object> update(long listingId, CreateCmd cmd) {
        if (cmd.title() == null || cmd.title().isBlank()) throw BizException.param("标题不能为空");
        if (cmd.monthlyRent() == null || cmd.monthlyRent().signum() <= 0) throw BizException.param("月租金必须大于 0");
        int updated = jdbc.update("update bp_listing set title=?, description=?, monthly_rent=?, "
                        + "deposit_amount=?, cover_url=?, update_time=now() "
                        + "where id=? and tenant_id=? and is_deleted=0",
                cmd.title().trim(), cmd.description(), cmd.monthlyRent(),
                cmd.depositAmount() == null ? BigDecimal.ZERO : cmd.depositAmount(), cmd.coverUrl(),
                listingId, TenantContext.require());
        if (updated == 0) throw BizException.notFound("展示不存在");
        return Map.of("id", listingId, "title", cmd.title());
    }

'''
marker='''    public record CreateCmd('''
if marker not in s: raise SystemExit('marker')
s=s.replace(marker,insert+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\main\java\com\yundao\platform\controller\ListingController.java'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    @PostMapping("/listings/{listingId}/publish")''','''    @PostMapping("/listings/{listingId}/update")
    public R<Map<String, Object>> update(@PathVariable long listingId,
                                         @RequestBody ListingService.CreateCmd cmd) {
        permissions.require("listing:manage");
        return R.ok(service.update(listingId, cmd));
    }

    @PostMapping("/listings/{listingId}/publish")''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('listing backend')
