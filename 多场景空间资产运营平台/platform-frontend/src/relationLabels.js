const labels = {
  TENANT: '承租人', FAMILY: '家庭成员', COHABITANT: '同住人', OWNER: '产权人',
  SPOUSE: '配偶', CHILD: '子女', PARENT: '父母', OTHER: '其他'
}
export function relationLabel(value) { return labels[value] || value || '-' }
export function relationStatusLabel(value) {
  return ({ ACTIVE: '有效', INACTIVE: '已结束', ENDED: '已结束' })[value] || value || '-'
}
