# -*- coding: utf-8 -*-
"""修正回调幂等键、表计收费项映射、指令审批与操作人。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def patch(rel, old, new, count=1):
    path = os.path.join(BK, rel)
    s = io.open(path, encoding='utf-8', errors='replace').read()
    if new in s:
        print('已包含', rel)
        return
    if old not in s:
        print('!! 未找到锚点', rel)
        return
    io.open(path, 'w', encoding='utf-8', newline='').write(s.replace(old, new, count))
    print('已修改', rel)


# 1) 回调：先解析再落日志，事件号缺省用 nonce，避免同类型日志互相顶掉
patch('iot/gateway/IotCallbackService.java',
      '''            JsonNode node = json.readTree(body.isBlank() ? "{}" : body);
            String eventId = text(node, "eventId");
            IotCallbackLog cl = saveLog(tenantId, action, appId, eventId, 1, body, sourceIp,
                    "RECEIVED", null, 0);''',
      '''            JsonNode node = json.readTree(body.isBlank() ? "{}" : body);
            String eventId = text(node, "eventId");
            if (eventId == null || eventId.isBlank()) {
                // 非事件类回调没有 eventId：用 nonce 作为日志幂等键
                eventId = (nonce == null || nonce.isBlank())
                        ? "T" + System.nanoTime() : "N:" + nonce;
            }
            IotCallbackLog cl = saveLog(tenantId, action, appId, eventId, 1, body, sourceIp,
                    "RECEIVED", null, 0);''')

# 验签失败日志也用 nonce 兜底，避免唯一键冲突
patch('iot/gateway/IotCallbackService.java',
      '''            saveLog(tenantId, action, appId, null, 0, body, sourceIp, "REJECTED", "验签失败", 0);''',
      '''            saveLog(tenantId, action, appId,
                    (nonce == null || nonce.isBlank()) ? "S" + System.nanoTime() : "N:" + nonce,
                    0, body, sourceIp, "REJECTED", "验签失败", 0);''')

# 2) 表计：按 meterType 找 METER 收费项目
patch('iot/gateway/IotCallbackService.java',
      '''    private Long findFeeItemId(String meterType) {
        if (meterType == null) {
            return null;
        }
        // ELEC / WATER / GAS / HEAT → 收费项目编码前缀约定
        return null;
    }''',
      '''    private Long findFeeItemId(String meterType) {
        if (meterType == null) {
            return null;
        }
        // 表计类型 → 收费项目编码约定：ELEC/WATER/GAS/HEAT
        java.util.List<String> codes = switch (meterType.toUpperCase()) {
            case "ELEC" -> java.util.List.of("ELEC", "ELECTRIC", "电费");
            case "WATER" -> java.util.List.of("WATER", "水费");
            case "GAS" -> java.util.List.of("GAS", "燃气费");
            case "HEAT" -> java.util.List.of("HEAT", "热力费");
            default -> java.util.List.of(meterType.toUpperCase());
        };
        for (String code : codes) {
            FinFeeItem item = feeItemMapper.selectOne(new LambdaQueryWrapper<FinFeeItem>()
                    .eq(FinFeeItem::getItemCode, code).last("LIMIT 1"));
            if (item != null) {
                return item.getId();
            }
        }
        // 兜底：任意按抄表计费的项目
        FinFeeItem any = feeItemMapper.selectOne(new LambdaQueryWrapper<FinFeeItem>()
                .eq(FinFeeItem::getCalcMode, "METER")
                .eq(FinFeeItem::getStatus, "ENABLED").last("LIMIT 1"));
        return any == null ? null : any.getId();
    }''')

# 注入 FinFeeItemMapper
patch('iot/gateway/IotCallbackService.java',
      'import com.yundao.bp.fin.mapper.FinMeterReadingMapper;',
      '''import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.mapper.FinFeeItemMapper;
import com.yundao.bp.fin.mapper.FinMeterReadingMapper;''')

patch('iot/gateway/IotCallbackService.java',
      '    private final AssetHouseMapper houseMapper;',
      '''    private final AssetHouseMapper houseMapper;
    private final FinFeeItemMapper feeItemMapper;''')

patch('iot/gateway/IotCallbackService.java',
      'FinMeterReadingMapper meterMapper, AssetHouseMapper houseMapper) {',
      '''FinMeterReadingMapper meterMapper, AssetHouseMapper houseMapper,
                              FinFeeItemMapper feeItemMapper) {''')

patch('iot/gateway/IotCallbackService.java',
      '        this.houseMapper = houseMapper;',
      '''        this.houseMapper = houseMapper;
        this.feeItemMapper = feeItemMapper;''')

# 3) 指令：操作人、拉合闸需审批后才下发
patch('dev/service/impl/DevCommandServiceImpl.java',
      '        c.setOperatorName(null);',
      '''        com.yundao.bp.iam.security.LoginUser u =
                com.yundao.bp.iam.security.LoginUser.get();
        c.setOperatorName(u == null ? null
                : (u.realName() == null ? u.username() : u.realName()));''')

patch('dev/service/impl/DevCommandServiceImpl.java',
      '''        mapper.insert(c);
        dispatch(id);
        return mapper.selectById(id);''',
      '''        mapper.insert(c);
        // 拉合闸需审批通过后再下发
        if (!"METER_SWITCH".equals(commandType)) {
            dispatch(id);
        }
        return mapper.selectById(id);''')

# 4) 新增审批接口
patch('dev/service/DevCommandService.java',
      '    DevCommand cancel(Long id);',
      '''    DevCommand cancel(Long id);

    /** 拉合闸审批（approve=true 通过并下发；false 驳回）。 */
    DevCommand approve(Long id, boolean approve);''')

patch('dev/service/impl/DevCommandServiceImpl.java',
      '    @Override\n    @Transactional(rollbackFor = Exception.class)\n    public void dispatch(Long id) {',
      '''    @Override
    @Transactional(rollbackFor = Exception.class)
    public DevCommand approve(Long id, boolean approve) {
        DevCommand c = get(id);
        if (!"METER_SWITCH".equals(c.getCommandType())) {
            throw BizException.paramInvalid("仅拉合闸指令需要审批");
        }
        if (!"PENDING".equals(c.getApproveStatus())) {
            throw BizException.stateConflict("该指令已审批过");
        }
        c.setApproveStatus(approve ? "APPROVED" : "REJECTED");
        c.setApproveBy(TenantContext.userId());
        c.setApproveTime(LocalDateTime.now());
        c.setUpdateTime(LocalDateTime.now());
        if (!approve) {
            c.setStatus("CANCELED");
            c.setResultMsg("审批驳回");
            mapper.updateById(c);
            return c;
        }
        mapper.updateById(c);
        dispatch(id);
        return mapper.selectById(id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispatch(Long id) {''')

patch('dev/controller/DevCommandController.java',
      '''    @RequirePerm("dev:command:retry")
    @PostMapping("/{id}/cancel")''',
      '''    @RequirePerm("dev:command:retry")
    @PostMapping("/{id}/approve")
    public R<DevCommand> approve(@PathVariable Long id,
                                 @RequestParam(defaultValue = "true") boolean approve) {
        return R.ok(service.approve(id, approve));
    }

    @RequirePerm("dev:command:retry")
    @PostMapping("/{id}/cancel")''')

print('修正完成')
