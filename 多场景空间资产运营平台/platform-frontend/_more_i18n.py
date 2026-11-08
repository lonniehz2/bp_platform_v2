import io,json
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
more={
'计费项目':'Fee Items','新增计费项':'Add Fee Item','计费项目列表':'Fee Items','停用后不再用于新账单':'Disabled items are not used for new bills','费用编码':'Fee Code','费用名称':'Fee Name','水费':'Water','电费':'Electricity','燃气费':'Gas','服务费':'Service Fee','其他':'Other','按月':'Monthly','按季':'Quarterly','按年':'Yearly','一次性':'One-time','税率':'Tax Rate','单价':'Unit Price','单位':'Unit','类型':'Type','周期':'Cycle','状态':'Status','操作':'Actions','停用':'Disable','启用':'Enable','公共租赁':'Public Rental','保障性租赁':'Affordable Rental','人才公寓':'Talent Apartment','宿舍':'Dormitory','配租公示':'Allocation Notice','资格公示':'Qualification Notice','退出公示':'Exit Notice','政策公示':'Policy Notice','新建公示':'New Notice','公示列表':'Notices','已发布':'Published','草稿':'Draft','关闭':'Close'
}
marker='for (const [k, v] of Object.entries(extra))'
block='Object.assign(extra, '+json.dumps(more,ensure_ascii=False,indent=2)+')\n'
s=s.replace(marker,block+marker,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('common translations')
