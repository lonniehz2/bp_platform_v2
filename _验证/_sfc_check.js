const fs = require('fs')
const path = require('path')
const { parse, compileTemplate } = require('@vue/compiler-sfc')

const file = path.join(__dirname, '..', 'frontend', 'src', 'views', 'FeeItems.vue')
const src = fs.readFileSync(file, 'utf8')
const { descriptor, errors } = parse(src, { filename: file })
console.log('parse errors:', errors.map((e) => String(e.message || e)))
const tpl = descriptor.template
const r = compileTemplate({ source: tpl.content, filename: file, id: 'x' })
console.log('template errors:', r.errors.map((e) => String(e.message || e)))
