import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grab import grab

targets = [
    ("nc163_gongzufang", "https://www.163.com/dy/article/K8UPVB4T0538L41J.html"),
    ("nc163_baozhang_jjfa", "https://www.163.com/dy/article/K5IN1K4G0538L41J.html"),
    ("m_news479", "https://m.byteox.com/news_479.html"),
    ("news43jiaju", "https://news.43jiaju.cn/n/122720.html"),
    ("m_home", "https://m.byteox.com/"),
]
for name, url in targets:
    grab(url, name)
    time.sleep(1)
