import { i18n } from './i18n'

export function enumLabel(value, domain = '') {
  if (value === null || value === undefined || value === '') return '-'
  const code = String(value).toUpperCase()
  if (domain) {
    const domainKey = `domain.${domain}.${code}`
    if (i18n.global.te(domainKey)) return i18n.global.t(domainKey)
  }
  if (/^CONTRACT_SCOPE_\d+$/.test(code)) return i18n.global.t('audit.contractScope')
  if (/^APPROVE_CONTRACT_\d+$/.test(code)) return i18n.global.t('audit.approveContract')
  for (const key of [`enum.${code}`, `status.${code}`]) {
    if (i18n.global.te(key)) return i18n.global.t(key)
  }
  return value
}

export function statusLabel(value) {
  return enumLabel(value)
}

export function enumText(value) {
  return String(value ?? '').replace(/[A-Z][A-Z0-9_]{2,}/g, code => {
    if (/^APPROVE_CONTRACT_\d+$/.test(code)) {
      return i18n.global.te('audit.approveContract') ? i18n.global.t('audit.approveContract') : code
    }
    if (/^CONTRACT_SCOPE_\d+$/.test(code)) {
      return i18n.global.te('audit.contractScope') ? i18n.global.t('audit.contractScope') : code
    }
    const key = `enum.${code}`
    return i18n.global.te(key) ? i18n.global.t(key) : code
  })
}
