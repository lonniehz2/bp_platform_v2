import io
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const originalText = new Map()","const originalText = new Map()\nconst lastTranslated = new WeakMap()")
s=s.replace("  if (!key) return\n  if (!originalText.has(node)) originalText.set(node, raw)","  if (!key) return\n  if (node.nodeValue === lastTranslated.get(node)) return\n  if (!originalText.has(node)) originalText.set(node, raw)")
s=s.replace("    translated.add(node)\n    return","    translated.add(node)\n    lastTranslated.set(node, node.nodeValue)\n    return")
s=s.replace("    node.nodeValue = originalText.get(node)\n    translated.delete(node)","    node.nodeValue = originalText.get(node)\n    translated.delete(node)\n    lastTranslated.delete(node)")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('loop fix')
