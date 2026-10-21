import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grab import grab

targets = [
    ("zentong_813358", "https://bbs.zentong.com/t813358-1"),
    ("zhihu_2017902922818663168", "https://zhuanlan.zhihu.com/p/2017902922818663168"),
    ("yun88_reo", "https://www.yun88.com/product/reo"),
]
for name, url in targets:
    grab(url, name)
    time.sleep(1)
