# -*- coding: utf-8 -*-
"""设备告警页三处修复：
  1) 统计与列表口径不一致 → stats 接受同样的筛选条件
  2) 详情 body 是 JSON 字符串 → 前端格式化为「键：值」
  3) 「告警类型 6」含义不清 → 改为「当前类型数 / 系统支持 6 种」
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------------- 1) 后端 stats 支持筛选 ----------------
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'dev', 'controller', 'DevEventController.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

OLD_STATS = """    /** 告警统计：按类型与级别。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/stats")
    public R<Map<String, Object>> stats(@RequestParam(required = false) Boolean unhandledOnly) {
        LambdaQueryWrapper<DevEvent> qw = new LambdaQueryWrapper<>();
        if (Boolean.TRUE.equals(unhandledOnly)) {
            qw.eq(DevEvent::getHandled, 0);
        }
        List<DevEvent> all = mapper.selectList(qw);"""

NEW_STATS = """    /** 告警统计：按类型与级别；筛选条件与列表一致，保证「总数」与列表条数对得上。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/stats")
    public R<Map<String, Object>> stats(
            @RequestParam(required = false) String deviceId,
            @RequestParam(required = false) String identifier,
            @RequestParam(required = false) String eventLevel,
            @RequestParam(required = false) Integer handled,
            @RequestParam(required = false) Boolean alarmOnly,
            @RequestParam(required = false) Boolean unhandledOnly) {
        LambdaQueryWrapper<DevEvent> qw = buildQuery(deviceId, identifier, eventLevel,
                handled, alarmOnly);
        if (Boolean.TRUE.equals(unhandledOnly)) {
            qw.eq(DevEvent::getHandled, 0);
        }
        List<DevEvent> all = mapper.selectList(qw);"""

if OLD_STATS in s:
    s = s.replace(OLD_STATS, NEW_STATS, 1)
    print('后端 stats 已支持筛选')

# 输出补 typeCount（当前出现类型数）
OLD_OUT = """        out.put("byType", byType);
        out.put("byLevel", byLevel);"""
NEW_OUT = """        out.put("byType", byType);
        out.put("byLevel", byLevel);
        out.put("typeCount", byType.size());"""
if OLD_OUT in s:
    s = s.replace(OLD_OUT, NEW_OUT, 1)
    print('后端 stats 增加 typeCount')

# 抽公共查询条件（列表与统计共用）
OLD_PAGE_QW = """        LambdaQueryWrapper<DevEvent> qw = new LambdaQueryWrapper<DevEvent>()
                .eq(deviceId != null && !deviceId.isBlank(), DevEvent::getDeviceId, deviceId)
                .eq(identifier != null && !identifier.isBlank(), DevEvent::getIdentifier, identifier)
                .eq(eventLevel != null && !eventLevel.isBlank(), DevEvent::getEventLevel, eventLevel)
                .eq(handled != null, DevEvent::getHandled, handled)
                .orderByDesc(DevEvent::getEventTime)
                .orderByDesc(DevEvent::getId);
        if (Boolean.TRUE.equals(alarmOnly)) {
            List<String> alarms = new ArrayList<>();
            for (DevEventType t : DevEventType.values()) {
                if (t.alarm()) {
                    alarms.add(t.name());
                }
            }
            qw.in(DevEvent::getIdentifier, alarms);
        }
        IPage<DevEvent> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);"""
NEW_PAGE_QW = """        LambdaQueryWrapper<DevEvent> qw = buildQuery(deviceId, identifier, eventLevel,
                handled, alarmOnly)
                .orderByDesc(DevEvent::getEventTime)
                .orderByDesc(DevEvent::getId);
        IPage<DevEvent> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);"""
if OLD_PAGE_QW in s:
    s = s.replace(OLD_PAGE_QW, NEW_PAGE_QW, 1)
    print('列表与统计共用查询条件')

# 追加 buildQuery（放在 report 之前）
HELPER = '''    /** 列表与统计共用的筛选条件，避免两处口径不一致。 */
    private LambdaQueryWrapper<DevEvent> buildQuery(String deviceId, String identifier,
                                                    String eventLevel, Integer handled,
                                                    Boolean alarmOnly) {
        LambdaQueryWrapper<DevEvent> qw = new LambdaQueryWrapper<DevEvent>()
                .eq(deviceId != null && !deviceId.isBlank(), DevEvent::getDeviceId, deviceId)
                .eq(identifier != null && !identifier.isBlank(),
                        DevEvent::getIdentifier, identifier)
                .eq(eventLevel != null && !eventLevel.isBlank(),
                        DevEvent::getEventLevel, eventLevel)
                .eq(handled != null, DevEvent::getHandled, handled);
        if (Boolean.TRUE.equals(alarmOnly)) {
            List<String> alarms = new ArrayList<>();
            for (DevEventType t : DevEventType.values()) {
                if (t.alarm()) {
                    alarms.add(t.name());
                }
            }
            qw.in(DevEvent::getIdentifier, alarms);
        }
        return qw;
    }

'''
if 'private LambdaQueryWrapper<DevEvent> buildQuery(' not in s:
    s = s.replace('    /** 事件上报（IoT 回调）。', HELPER + '    /** 事件上报（IoT 回调）。', 1)
    print('后端已抽 buildQuery')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
