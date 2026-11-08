import io
p=r'src\pages\Projects.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("    if (!form.orgCode.trim()) throw new Error('请填写项目编码')","    if (!form.orgCode.trim()) throw new Error('请填写项目编码')\n    if (!form.orgName.trim()) throw new Error('请填写项目名称')\n    if (form.contactPhone && !/^1\\d{10}$/.test(form.contactPhone)) throw new Error('联系电话需为 11 位手机号')\n    if (Number(form.totalArea) < 0 || Number(form.landArea) < 0) throw new Error('面积不能为负数')\n    if (form.buildYear && (form.buildYear < 1900 || form.buildYear > 2100)) throw new Error('建成年份需在 1900-2100 之间')")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\pages\Contracts.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("    if (!form.contractNo.trim()) throw new Error('请填写合同编号')","    if (!form.contractNo.trim()) throw new Error('请填写合同编号')\n    if (!form.houseId || !form.personId) throw new Error('请选择房屋和承租人')\n    if (!form.startDate || !form.endDate) throw new Error('请选择合同起止日期')\n    if (new Date(form.endDate) <= new Date(form.startDate)) throw new Error('合同结束日期必须晚于开始日期')\n    if (Number(form.rentAmount) < 0 || Number(form.depositAmount) < 0) throw new Error('租金和押金不能为负数')\n    if (Number(form.billDay) < 1 || Number(form.billDay) > 28) throw new Error('账单日需在 1-28 之间')")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\pages\Persons.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("    if (!form.personCode.trim() || !form.personName.trim()) throw new Error('请填写人员编码和姓名')","    if (!form.personCode.trim() || !form.personName.trim()) throw new Error('请填写人员编码和姓名')\n    if (form.phone && !/^1\\d{10}$/.test(form.phone)) throw new Error('手机号需为 11 位号码')\n    if (form.birthDate && new Date(form.birthDate) > new Date()) throw new Error('出生日期不能晚于今天')")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\pages\Applications.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("    if (!form.applicantPersonId) throw new Error('请选择申请人')","    if (!form.applicantPersonId) throw new Error('请选择申请人')\n    if (form.contactPhone && !/^1\\d{10}$/.test(form.contactPhone)) throw new Error('联系电话需为 11 位手机号')\n    if (Number(form.familySize) < 1 || Number(form.familySize) > 20) throw new Error('家庭人数需在 1-20 之间')")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\pages\Houses.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("async function saveEdit() {\n  try {","async function saveEdit() {\n  try {\n    if (Number(editForm.area) < 0 || Number(editForm.innerArea) < 0) throw new Error('面积不能为负数')\n    if (Number(editForm.floorNo) < 1 || Number(editForm.totalFloors) < 1 || Number(editForm.floorNo) > Number(editForm.totalFloors)) throw new Error('楼层需满足 1 ≤ 所在楼层 ≤ 总楼层')")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('validation')
