const labels = {
  DRAFT: '草稿',
  APPROVING: '审批中',
  ACTIVE: '生效中',
  TERMINATED: '已终止',
  DISCARDED: '已作废',
  WITHDRAWN: '已撤回',
  EXPIRED: '已到期'
}

export function contractStatusLabel(status) {
  return labels[status] || status || '-'
}

export function contractStatusTone(status) {
  if (status === 'ACTIVE') return 'green'
  if (status === 'APPROVING') return 'blue'
  if (status === 'DRAFT') return ''
  if (status === 'DISCARDED' || status === 'TERMINATED' || status === 'WITHDRAWN') return 'orange'
  return ''
}
