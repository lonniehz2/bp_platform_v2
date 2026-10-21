import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grab import grab
for name, url in [
    ("nc163_guoqi_bzf", "https://www.163.com/dy/article/L1B15GRO0538L41J.html"),
    ("nc163_quanfangwei", "https://m.163.com/dy/article/KI19N2O10538L41J.html"),
]:
    grab(url, name)
    time.sleep(1)
