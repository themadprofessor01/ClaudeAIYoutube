"""Convert Blender renders (PNG) into the JPEG plates the compositions load.

usage: python3 tools/plates.py [renders|renders_draft]   → assets/plates/<key>.jpg
"""
import os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, sys.argv[1] if len(sys.argv) > 1 else "renders")
dst = os.path.join(ROOT, "assets", "plates")
os.makedirs(dst, exist_ok=True)
n = 0
for f in sorted(os.listdir(src)):
    if not f.endswith(".png"):
        continue
    out = os.path.join(dst, f[:-4] + ".jpg")
    if os.path.exists(out) and os.path.getmtime(out) > os.path.getmtime(os.path.join(src, f)):
        continue
    Image.open(os.path.join(src, f)).convert("RGB").save(out, quality=90, optimize=True, progressive=True)
    n += 1
print(n, "plates written to", dst)
