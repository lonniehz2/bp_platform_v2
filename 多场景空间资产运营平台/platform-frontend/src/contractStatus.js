import { i18n } from './i18n'

const labels = {}


export function contractStatusLabel(status) {
  const key = `status.${status}`
  return i18n.global.te(key) ? i18n.global.t(key) : (labels[status] || status || '-')
}

export function contractStatusTone(status) {
  if (status === 'ACTIVE') return 'green'
  if (status === 'APPROVING') return 'blue'
  if (status === 'DRAFT') return ''
  if (status === 'DISCARDED' || status === 'TERMINATED' || status === 'WITHDRAWN') return 'orange'
  return ''
}
