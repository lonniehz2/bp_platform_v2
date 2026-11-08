import io
p=r'src\styles.css'
s=io.open(p,encoding='utf-8').read()
if '.receipt' not in s:
 s += '''

.receipt { padding: 16px; border: 1px dashed var(--line-strong); }
.receipt h3 { text-align: center; margin: 4px 0 18px; }
.receipt p { margin: 8px 0; }
@media print {
  body * { visibility: hidden; }
  .receipt-box, .receipt-box * { visibility: visible; }
  .receipt-box { position: absolute; inset: 0; margin: 0; box-shadow: none; border: 0; }
  .no-print { display: none !important; }
}
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('receipt css')
