import { createI18n } from 'vue-i18n'

const messages = {
  'zh-CN': {
    nav: {
      dashboard: '工作台',
      asset: '项目与资产',
      search: '统一查询',
      person: '客户与人员',
      application: '申请与轮候',
      contract: '合同与租赁',
      changes: '合同变更',
      qualification: '资格复核',
      billing: '收费与账务',
      deposits: '押金与补贴',
      arrears: '欠费清单',
      cashflow: '资金流水',
      reports: '运营报表',
      fee: '计费项目',
      meter: '计量与能耗',
      device: '设备与授权',
      service: '服务与工单',
      access: '访客通行',
      complaint: '投诉与申诉',
      publicity: '公示管理',
      alert: '风险告警',
      credit: '信用惩戒',
      shortrent: '短租订单',
      open: '开放平台',
      message: '消息中心',
      gov: '监管报送',
      users: '用户管理',
      audit: '审批中心',
      config: '菜单与角色',
      migration: '迁移异常',
      help: '使用帮助'
    },
    login: {
      brand: '多场景空间资产运营平台',
      en: 'Multi-scene Space Asset Platform',
      slogan: '统一空间资产、合同、收费与授权，服务保障房、物业、公寓、办公、酒店与校园。',
      flow: '申请到收款闭环',
      flowDesc: '申请、轮候、配租、合同、账单、收款全流程',
      assetTitle: '空间资产统一建模',
      assetDesc: '模板、资产类型、房屋与设备统一管理',
      grantTitle: '人员与钥匙包',
      grantDesc: '空间授权、设备授权、有效期与撤销',
      multiTitle: '多场景扩展',
      multiDesc: '保障房、物业、公寓、办公、酒店、校园',
      welcome: '欢迎登录',
      subtitle: '请使用平台账号进入运营工作台',
      tenant: '租户',
      username: '用户名',
      password: '密码',
      submit: '登录',
      demo: '演示账号',
      platform: '运营平台'
    },
    common: {
      project: '项目',
      logout: '退出',
      light: '浅色',
      dark: '深色',
      language: '语言'
    }
  },
  'en-US': {
    nav: {
      dashboard: 'Dashboard',
      asset: 'Projects & Assets',
      search: 'Search',
      person: 'Customers & People',
      application: 'Applications',
      contract: 'Contracts',
      changes: 'Contract Changes',
      qualification: 'Qualification Review',
      billing: 'Billing',
      deposits: 'Deposits & Subsidies',
      arrears: 'Arrears',
      cashflow: 'Cash Flow',
      reports: 'Reports',
      fee: 'Fee Items',
      meter: 'Meters & Energy',
      device: 'Devices & Access',
      service: 'Service Orders',
      access: 'Access Records',
      complaint: 'Complaints & Appeals',
      publicity: 'Publicity',
      alert: 'Risk Alerts',
      credit: 'Credit Discipline',
      shortrent: 'Short Rent',
      open: 'Open Platform',
      message: 'Messages',
      gov: 'Regulatory Reporting',
      users: 'Users',
      audit: 'Approvals',
      config: 'Menus & Roles',
      migration: 'Migration Exceptions',
      help: 'Help'
    },
    login: {
      brand: 'Multi-scene Space Asset Platform',
      en: 'Multi-scene Space Asset Platform',
      slogan: 'Unified space assets, contracts, billing and access for housing, property, apartment, office, hotel and campus.',
      flow: 'Application to receipt',
      flowDesc: 'Application, waitlist, allocation, contract, bill and payment',
      assetTitle: 'Unified asset model',
      assetDesc: 'Templates, asset types, houses and devices',
      grantTitle: 'People and keyrings',
      grantDesc: 'Space grants, device grants, validity and revocation',
      multiTitle: 'Multi-scene ready',
      multiDesc: 'Guarantee housing, property, apartment, office, hotel, campus',
      welcome: 'Sign in',
      subtitle: 'Use your platform account to enter the workspace',
      tenant: 'Tenant',
      username: 'Username',
      password: 'Password',
      submit: 'Sign in',
      demo: 'Demo account',
      platform: 'Platform'
    },
    common: {
      project: 'Project',
      logout: 'Sign out',
      light: 'Light',
      dark: 'Dark',
      language: 'Language'
    }
  }
}

const queryLocale = new URLSearchParams(location.search).get('lang')
const saved = queryLocale === 'en' || queryLocale === 'en-US' ? 'en-US' : (localStorage.getItem('platformLocale') || 'zh-CN')

export const i18n = createI18n({
  legacy: false,
  locale: saved,
  fallbackLocale: 'zh-CN',
  messages
})

export function setLocale(locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('platformLocale', locale)
}
