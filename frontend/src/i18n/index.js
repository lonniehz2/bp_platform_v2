import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'

export const SUPPORTED_LOCALES = ['zh-CN', 'en-US']
const STORAGE_KEY = 'bp_locale'

export function normalizeLocale(tag) {
  if (!tag) return 'zh-CN'
  const t = String(tag).replace('_', '-').toLowerCase()
  return t.startsWith('en') ? 'en-US' : 'zh-CN'
}

function initialLocale() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) return normalizeLocale(saved)
  return 'zh-CN'
}

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale(),
  fallbackLocale: 'zh-CN',
  messages: { 'zh-CN': zhCN, 'en-US': enUS },
  missingWarn: false,
  fallbackWarn: false
})

export function getLocale() {
  return normalizeLocale(i18n.global.locale.value)
}

export function setLocale(tag) {
  const locale = normalizeLocale(tag)
  i18n.global.locale.value = locale
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.lang = locale
  return locale
}

document.documentElement.lang = getLocale()
