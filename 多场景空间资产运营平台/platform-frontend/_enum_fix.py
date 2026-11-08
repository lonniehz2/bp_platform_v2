import io
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
start=s.index('function translateTextNode(node) {')
end=s.index('function translateTree(root) {')
new='''function translateTextNode(node) {
  if (!node || node.nodeType !== 3) return
  const parent = node.parentElement
  if (!parent || ['SCRIPT', 'STYLE', 'TEXTAREA'].includes(parent.tagName)) return
  const raw = node.nodeValue || ''
  const key = raw.trim()
  if (!key) return
  if (!originalText.has(node)) originalText.set(node, raw)
  const target = currentLocale === 'zh-CN'
    ? enumZh[key]
    : (currentLocale === 'en-US' ? (enumEn[key] || dictionary.get(key) || patternTranslate(key)) : '')
  if (target) {
    if (node.nodeValue !== target) {
      const leading = raw.slice(0, raw.indexOf(key))
      const trailing = raw.slice(raw.indexOf(key) + key.length)
      node.nodeValue = leading + target + trailing
    }
    translated.add(node)
    return
  }
  if (translated.has(node)) {
    node.nodeValue = originalText.get(node)
    translated.delete(node)
  }
}

'''
s=s[:start]+new+s[end:]
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('enum zh fix')
