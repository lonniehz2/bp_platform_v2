# -*- coding: utf-8 -*-
"""OrgVO.from / create / update 补齐五级地址代码。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
IAM = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'iam')

# ---------- VO.from ----------
P = os.path.join(IAM, 'dto', 'OrgVO.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

if 'e.getProvinceCode()' not in s:
    # 先修正字段顺序：把代码字段放到 city/district/street/community 之后更清晰
    OLD_FIELDS = '''        String province,
        String provinceCode,
        String cityCode,
        String districtCode,
        String streetCode,
        String communityCode, String city, String district,
        String street, String community,'''
    NEW_FIELDS = '''        String province,
        String city,
        String district,
        String street,
        String community,
        String provinceCode,
        String cityCode,
        String districtCode,
        String streetCode,
        String communityCode,'''
    if OLD_FIELDS in s:
        s = s.replace(OLD_FIELDS, NEW_FIELDS, 1)

    OLD_FROM = '''                e.getProvince(), e.getCity(), e.getDistrict(), e.getStreet(),
                e.getCommunity(), e.getAddress(),'''
    NEW_FROM = '''                e.getProvince(), e.getCity(), e.getDistrict(), e.getStreet(),
                e.getCommunity(),
                e.getProvinceCode(), e.getCityCode(), e.getDistrictCode(),
                e.getStreetCode(), e.getCommunityCode(),
                e.getAddress(),'''
    if OLD_FROM in s:
        s = s.replace(OLD_FROM, NEW_FROM, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('OrgVO.from：已映射代码字段')

# ---------- create / update 写入代码 ----------
P = os.path.join(IAM, 'service', 'impl', 'OrgServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

if 'setProvinceCode' not in s:
    # create 中：e.setProvince(cmd.province()); 之后补代码
    s = s.replace('''                e.setProvince(cmd.province());''', '''                e.setProvince(cmd.province());
                e.setProvinceCode(cmd.provinceCode());
                e.setCityCode(cmd.cityCode());
                e.setDistrictCode(cmd.districtCode());
                e.setStreetCode(cmd.streetCode());
                e.setCommunityCode(cmd.communityCode());''')

    # 若 create 使用另一种赋值写法（setProvince 单行），兜底再试一次
    if 'setProvinceCode' not in s:
        s = s.replace('''        e.setProvince(cmd.province());''', '''        e.setProvince(cmd.province());
        e.setProvinceCode(cmd.provinceCode());
        e.setCityCode(cmd.cityCode());
        e.setDistrictCode(cmd.districtCode());
        e.setStreetCode(cmd.streetCode());
        e.setCommunityCode(cmd.communityCode());''')

    # update 中
    s = s.replace('''        e.setProvince(cmd.province());''', '''        e.setProvince(cmd.province());
        e.setProvinceCode(cmd.provinceCode());
        e.setCityCode(cmd.cityCode());
        e.setDistrictCode(cmd.districtCode());
        e.setStreetCode(cmd.streetCode());
        e.setCommunityCode(cmd.communityCode());''')

    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('OrgServiceImpl：create/update 已写代码字段')
else:
    print('已存在代码写入')
