export const deviceImportHeader = '组织编码,楼栋,单元,楼层,房间,床位内房,房源编号,房源名称,房源类型,建筑面积,设备编号,设备类型,设备名称,物理MAC'
export const deviceImportHeaderEn = 'Org Code (orgCode),Building,Unit,Floor,Room,Bed Room,House Code,House Name,House Type,Floor Area,Device Code,Device Type,Device Name,MAC'
export const deviceImportSample = (orgCode) => orgCode + ',A栋,1单元,1层,101室,,,101室,公租房,60,,门锁,101门锁,'

export const contractTemplate = (en = false) => en ? '\ufeffProject Code (projectCode),Contract No.,House Code,Person Code,Start Date,End Date,Monthly Rent,Deposit,Billing Cycle,Bill Day,Draft\n' : '\ufeff项目编码,合同编号,房屋编码,人员编码,开始日期,结束日期,月租金,押金,账单周期,账单日,草稿\nZZ0020,HT-001,101,P0001,2026-01-01,2026-12-31,1200,1200,MONTH,1,是\n'
export const userTemplate = (en = false) => en ? '\ufeffUsername,Password,Name,Role Code\n' : '\ufeff用户名,密码,姓名,角色编码\nzhangsan,123456,张三,ASSET_CLERK\n'
export const deviceGrantTemplate = (en = false) => en ? '\ufeffProject Code (projectCode),Person Code,Device Code,Start Date,End Date,Access Level\n' : '\ufeff项目编码,人员编码,设备编码,开始日期,结束日期,权限级别\nZZ0020,P0001,LOCK-001,2026-01-01,2026-12-31,OPEN\n'
export const grantTemplate = (en = false) => en ? '\ufeffProject Code (projectCode),Person Code,Space Code,Access Level,Start Date,End Date\n' : '\ufeff项目编码,人员编码,空间编码,权限级别,开始日期,结束日期\nZZ0020,P0001,101,OPEN,2026-01-01,2026-12-31\n'
export const bindingTemplate = (en = false) => en ? '\ufeffProject Code (projectCode),Device Code,Space Code\n' : '\ufeff项目编码,设备编码,空间编码\nZZ0020,LOCK-001,101\n'
export const relationTemplate = (en = false) => en ? '\ufeffProject Code (projectCode),Person Code,House Code,Relation Type,Start Date,End Date,Primary\n' : '\ufeff项目编码,人员编码,房屋编码,关系类型,开始日期,结束日期,是否主要关系\nZZ0020,P0001,101,TENANT,2026-01-01,2026-12-31,是\n'
export const spaceTemplate = (en = false) => en ? '\ufeffProject Code (projectCode),Parent Space Code,Space Code,Space Name,Space Type,Asset Type,Floor Area,Inner Area,Rentable\n' : '\ufeff项目编码,上级空间编码,空间编码,空间名称,空间类型,资产类型,建筑面积,套内面积,可出租\nZZ0020,A栋,1单元,1单元,UNIT,PUBLIC_RENTAL,0,0,否\nZZ0020,1单元,101,101室,ROOM,PUBLIC_RENTAL,60,52,是\n'
export const personTemplate = (en = false) => en ? '\ufeffPerson Code (personCode),Name,Phone,ID Mask,Person Type,Gender,Birth Date,Address,Employer,Emergency Contact,Remark\n' : '\ufeff人员编码,姓名,手机号,身份证脱敏,人员类型,性别,出生日期,地址,工作单位,紧急联系人,备注\nP0001,张三,13800000000,330***********1234,GUARANTEE_TENANT,MALE,1990-01-01,示例地址,示例单位,李四,导入示例\n'
export const govReportHeader = ['合同编号','承租人','房屋','开始日期','结束日期','月租金','状态']
export const govReportHeaderEn = ['Contract No.','Tenant','House','Start Date','End Date','Monthly Rent','Status']
