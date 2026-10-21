import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grab import grab

B = "https://www.byteox.com"
pages = [
    ("affordableHousing", "/affordableHousing"),
    ("longRent", "/longRent"),
    ("serviced", "/serviced"),
    ("shortRent", "/shortRent"),
    ("corporateDorm", "/corporateDorm"),
    ("businessPark", "/businessPark"),
    ("talentHousing", "/talentHousing"),
    ("studentDorm", "/studentDorm"),
    ("about", "/about"),
    ("news", "/resourceServices/news"),
    ("download", "/resourceServices/download"),
    ("prod_jdf", "/product/jdf"),
    ("prod_tfzs", "/product/tfzs"),
    ("prod_yxs", "/product/yxs"),
]
for name, path in pages:
    grab(B + path, name)
    time.sleep(0.5)

for t in range(1, 16):
    grab(f"{B}/product/product?type={t}", f"prod_type{t}")
    time.sleep(0.4)
