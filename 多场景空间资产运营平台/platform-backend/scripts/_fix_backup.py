import io
p='DbBackup.java'
s=io.open(p,encoding='utf-8').read().replace('characterEncoding=utf8mb4','characterEncoding=UTF-8')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('fixed')
