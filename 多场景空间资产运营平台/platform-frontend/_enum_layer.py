import io,json
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
enum_zh={
'GUARANTEE':'保障房','PUBLIC_RENTAL':'公共租赁','AFFORDABLE_RENTAL':'保障性租赁','TALENT_APARTMENT':'人才公寓','DORMITORY':'宿舍',
'ENABLED':'启用','DISABLED':'停用','ACTIVE':'有效','TERMINATED':'已终止','DRAFT':'草稿','SUBMITTED':'已提交','APPROVED':'已通过','APPROVING':'审批中','REJECTED':'已驳回','WAITING':'等待中','ALLOCATED':'已配租','VACANT':'空置','OCCUPIED':'已入住','UNPAID':'未缴','PARTIAL':'部分缴','PAID':'已付','OVERDUE':'逾期','WAIVED':'已减免','CONTRACTED':'已签约','CANCELLED':'已取消','COMPLETED':'已完成','CONFIRMED':'已确认','CHECKED_IN':'已入住','PENDING':'待处理','PROCESSING':'处理中','RESOLVED':'已解决','IGNORED':'已忽略','CLOSED':'已关闭','SUCCESS':'成功','NORMAL':'正常','HIGH':'高','URGENT':'紧急','LOW':'低',
'RENT_CHANGE':'租金变更','TERM_CHANGE':'期限变更','ROOM_CHANGE':'换房','TERMINATION':'退租','LOCK':'门锁','METER':'水电表','ELEVATOR':'电梯','GATE':'门禁','BUILDING':'楼栋','UNIT':'单元','FLOOR':'楼层','ROOM':'房屋','INNER_ROOM':'内房','BED':'床位','AREA':'区域','WATER':'水表','ELECTRICITY':'电表','GAS':'燃气表',
'CASH':'现金','WECHAT':'微信','ALIPAY':'支付宝','BANK':'银行','OPEN':'开放','MANUAL':'手工','COMPLAINT':'投诉','APPEAL':'申诉','VISIT':'走访','RISK':'风险','DEVICE':'设备','OTHER':'其他','VIOLATION':'违规','ARREARS':'欠费','RENT':'租金','DEPOSIT':'押金','SERVICE':'服务费','MONTHLY':'按月','QUARTERLY':'按季','YEARLY':'按年','ONE_TIME':'一次性',
'ADMIN':'管理员','STAFF':'员工','TENANT':'租户','GUARANTEE_TENANT':'保障对象','FAMILY':'家庭成员','COHABITANT':'同住人','VISITOR':'访客','TALENT':'人才','GUARANTEE_ADMIN':'保障房管理员','GUARANTEE_MANAGER':'保障房经理','GUARANTEE_STEWARD':'保障房客服','GUARANTEE_FINANCE':'保障房财务'
}
enum_en={
'GUARANTEE':'Guarantee','PUBLIC_RENTAL':'Public Rental','AFFORDABLE_RENTAL':'Affordable Rental','TALENT_APARTMENT':'Talent Apartment','DORMITORY':'Dormitory',
'ENABLED':'Enabled','DISABLED':'Disabled','ACTIVE':'Active','TERMINATED':'Terminated','DRAFT':'Draft','SUBMITTED':'Submitted','APPROVED':'Approved','APPROVING':'Approving','REJECTED':'Rejected','WAITING':'Waiting','ALLOCATED':'Allocated','VACANT':'Vacant','OCCUPIED':'Occupied','UNPAID':'Unpaid','PARTIAL':'Partial','PAID':'Paid','OVERDUE':'Overdue','WAIVED':'Waived','CONTRACTED':'Contracted','CANCELLED':'Cancelled','COMPLETED':'Completed','CONFIRMED':'Confirmed','CHECKED_IN':'Checked in','PENDING':'Pending','PROCESSING':'Processing','RESOLVED':'Resolved','IGNORED':'Ignored','CLOSED':'Closed','SUCCESS':'Success','NORMAL':'Normal','HIGH':'High','URGENT':'Urgent','LOW':'Low',
'RENT_CHANGE':'Rent Change','TERM_CHANGE':'Term Change','ROOM_CHANGE':'Exchange','TERMINATION':'Termination','LOCK':'Lock','METER':'Meter','ELEVATOR':'Elevator','GATE':'Gate','BUILDING':'Building','UNIT':'Unit','FLOOR':'Floor','ROOM':'Room','INNER_ROOM':'Inner Room','BED':'Bed','AREA':'Area','WATER':'Water','ELECTRICITY':'Electricity','GAS':'Gas',
'CASH':'Cash','WECHAT':'WeChat','ALIPAY':'Alipay','BANK':'Bank','OPEN':'Open','MANUAL':'Manual','COMPLAINT':'Complaint','APPEAL':'Appeal','VISIT':'Visit','RISK':'Risk','DEVICE':'Device','OTHER':'Other','VIOLATION':'Violation','ARREARS':'Arrears','RENT':'Rent','DEPOSIT':'Deposit','SERVICE':'Service Fee','MONTHLY':'Monthly','QUARTERLY':'Quarterly','YEARLY':'Yearly','ONE_TIME':'One-time',
'ADMIN':'Admin','STAFF':'Staff','TENANT':'Tenant','GUARANTEE_TENANT':'Guarantee Tenant','FAMILY':'Family','COHABITANT':'Cohabitant','VISITOR':'Visitor','TALENT':'Talent'
}
# Insert enum maps before installPageI18n
marker='export function installPageI18n(locale)'
block='const enumZh = '+json.dumps(enum_zh,ensure_ascii=False,indent=2)+'\n\nconst enumEn = '+json.dumps(enum_en,ensure_ascii=False,indent=2)+'\n\n'
s=s.replace(marker,block+marker,1)
# Add enum check in translateTextNode before dictionary
s=s.replace("  const target = dictionary.get(key) || patternTranslate(key)","  const target = (currentLocale === 'zh-CN' ? enumZh[key] : enumEn[key]) || dictionary.get(key) || patternTranslate(key)")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('enum layer')
