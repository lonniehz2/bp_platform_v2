import { i18n } from './i18n'

const labels = {}

export function relationLabel(value) { const key = `relation.${value}`; return i18n.global.te(key) ? i18n.global.t(key) : (labels[value] || value || '-') }
export function relationStatusLabel(value) {
  const key = `relation.${value}`; return i18n.global.te(key) ? i18n.global.t(key) : (value || '-')
}
