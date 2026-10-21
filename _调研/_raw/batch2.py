import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grab import grab

targets = [
    ("yun88_9556", "https://www.yun88.com/product/9556.html"),
    ("nc163_baozufang", "https://www.163.com/dy/article/KOCHE9M30538L41J.html"),
    ("nc163_baozhangfang", "https://www.163.com/dy/article/JTOSE16K0538L41J.html"),
    ("m_customer", "https://m.byteox.com/customer"),
    ("baike_ymgj", "https://baike.baidu.com/item/%E5%AF%93%E7%9B%9F%E7%AE%A1%E5%AE%B6/61931896"),
]
for name, url in targets:
    grab(url, name)
    time.sleep(1)
