import { buildCsv } from '../src/reportsCsv.js'
const csv = buildCsv(['项目', '出租率'], [['演示项目', '66.7'], ['含"引号"', '0']])
const lines = csv.replace(/^\ufeff/, '').split('\n')
const failures = []
if (!csv.startsWith('\ufeff')) failures.push('缺少 UTF-8 BOM')
if (lines[0] !== '"项目","出租率"') failures.push('表头不正确')
if (lines[1] !== '"演示项目","66.7"') failures.push('普通行不正确')
if (lines[2] !== '"含""引号""","0"') failures.push('引号转义不正确')
if (failures.length) { failures.forEach(x => console.error(`[report-csv] ${x}`)); process.exit(1) }
console.log('[report-csv] 通过：BOM、表头、行数据和引号转义正确')
