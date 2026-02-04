import shutil
import os

src_dir = r"C:\Users\sky.lo\Desktop\CDU程式碼\CDU\250303\CDU Icon"
dst_dir = r"c:\Users\sky.lo\Desktop\CDU程式碼\CDU\250303\webUI\frontend\public\img\diagram"

mapping = {
    "冷卻液液位.png": "icon_level.png",
    "冷卻液溫度T.png": "icon_temp.png",
    "氣壓P.png": "icon_pressure.png"
}

for chi_name, eng_name in mapping.items():
    src = os.path.join(src_dir, chi_name)
    dst = os.path.join(dst_dir, eng_name)
    try:
        shutil.copy2(src, dst)
        print(f"Copied {src} to {dst}")
    except Exception as e:
        print(f"Error copying {chi_name}: {e}")
