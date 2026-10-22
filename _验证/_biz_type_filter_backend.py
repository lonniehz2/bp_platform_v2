# -*- coding: utf-8 -*-
"""多业态第一步：房源列表支持「业态（房源类型）」筛选（前后端打通）。

- 后端 HouseService.page 增加 houseType 参数（宿舍/公寓/酒店民宿/公租房…）
- 前端房源台账增加业态下拉，与类型标签联动过滤
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'asset')

# ---------- 1) Controller ----------
C = os.path.join(J, 'controller', 'HouseController.java')
s = io.open(C, encoding='utf-8').read()
if 'houseType' not in s.split('public R<PageResult<HouseVO>> page')[1][:400]:
    s = s.replace('''            @RequestParam(required = false) String houseStatus,
            @RequestParam(required = false) String keyword) {
        return R.ok(houseService.page(pageNum, pageSize, orgId, spaceId, houseStatus, keyword));''',
                  '''            @RequestParam(required = false) String houseStatus,
            @RequestParam(required = false) String houseType,
            @RequestParam(required = false) String keyword) {
        return R.ok(houseService.page(pageNum, pageSize, orgId, spaceId, houseStatus,
                houseType, keyword));''', 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('HouseController：已加 houseType 参数')

# ---------- 2) Service 接口 ----------
S = os.path.join(J, 'service', 'HouseService.java')
s = io.open(S, encoding='utf-8').read()
if 'houseStatus, String houseType' not in s:
    s = s.replace('String houseStatus, String keyword)',
                  'String houseStatus, String houseType, String keyword)', 1)
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('HouseService：签名已加 houseType')

# ---------- 3) 实现 ----------
I = os.path.join(J, 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'houseStatus, String houseType' not in s:
    s = s.replace('String houseStatus, String keyword)',
                  'String houseStatus, String houseType, String keyword)', 1)
    # 在 wrapper 里追加业态过滤：找 houseStatus 的 eq 处
    if '.eq(StringUtils.hasText(houseStatus), AssetHouse::getHouseStatus, houseStatus)' in s:
        s = s.replace('.eq(StringUtils.hasText(houseStatus), AssetHouse::getHouseStatus, houseStatus)',
                      '.eq(StringUtils.hasText(houseStatus), AssetHouse::getHouseStatus, houseStatus)\n'
                      '                .eq(StringUtils.hasText(houseType), AssetHouse::getHouseType, houseType)',
                      1)
    else:
        print('  未找到 houseStatus 过滤处，需人工确认')
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('HouseServiceImpl：已加业态过滤')

print('后端完成')
