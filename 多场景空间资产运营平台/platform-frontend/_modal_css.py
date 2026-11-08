import io
p=r'src\styles.css'
s=io.open(p,encoding='utf-8').read()
if '.modal-mask' not in s:
 s += '''

.modal-mask {
  position: fixed; inset: 0; background: rgba(0, 0, 0, .45); z-index: 100;
  display: grid; place-items: center;
}
.modal {
  width: min(420px, calc(100vw - 32px)); background: var(--panel); border: 1px solid var(--line);
  border-radius: 4px; padding: 18px; box-shadow: 0 10px 30px rgba(0, 0, 0, .2);
}
.modal .field { margin-bottom: 10px; }
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('modal css')
