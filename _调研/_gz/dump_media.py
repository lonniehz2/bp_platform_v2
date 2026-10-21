# -*- coding: utf-8 -*-
import zipfile, os, shutil
p = r"D:\Work\业务平台开发\_调研\公租房管理方案.docx"
out = r"D:\Work\业务平台开发\_调研\_公租房图"
os.makedirs(out, exist_ok=True)
z = zipfile.ZipFile(p)
for n in z.namelist():
    if n.startswith('word/media/'):
        tgt = os.path.join(out, os.path.basename(n))
        with open(tgt,'wb') as f:
            f.write(z.read(n))
        print(os.path.basename(n), os.path.getsize(tgt))
