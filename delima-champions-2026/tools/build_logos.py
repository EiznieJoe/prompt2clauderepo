"""Bina aset logo daripada poster rujukan.

Logo dipotong terus daripada piksel poster (tiada lukisan semula). Topeng
(assets/source/mask-*.png) dijana dengan GrabCut + pembersihan tepi; skrip ini
menukar topeng itu kepada PNG lutsinar 2x dan lapisan bevel untuk rawatan 3D.

    python3 tools/build_logos.py
"""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

POSTER = "assets/source/poster-rujukan.png"
LOGOS = {
    # nama: (kotak potong dalam poster, topeng)
    "delima": ((760, 40, 1560, 820), "assets/source/mask-delima.png"),
    "sekolah": ((260, 40, 580, 390), "assets/source/mask-sekolah.png"),
}
SCALE = 1.5

poster = Image.open(POSTER).convert("RGB")
for name, (box, mask_path) in LOGOS.items():
    rgb = poster.crop(box)
    mask = Image.open(mask_path).convert("L")
    # trim to the mask's bounding box + small pad
    bb = mask.getbbox()
    pad = 4
    bb = (max(bb[0] - pad, 0), max(bb[1] - pad, 0), min(bb[2] + pad, mask.width), min(bb[3] + pad, mask.height))
    rgb, mask = rgb.crop(bb), mask.crop(bb)
    size = (round(rgb.width * SCALE), round(rgb.height * SCALE))
    rgb = rgb.resize(size, Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    # soft 1px edge so the cut never shows a hard stair-step
    mask = mask.resize(size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.9))
    a = np.asarray(mask).astype(np.float32) / 255.0
    a = np.clip((a - 0.5) * 2.2 + 0.5, 0, 1)
    front = np.dstack([np.asarray(rgb), (a * 255).astype(np.uint8)])
    Image.fromarray(front, "RGBA").save(f"assets/logos/{name}.png", optimize=True)

    # bevel: light from top-left on a ~10px band inside the silhouette edge
    solid = a > 0.5
    dist = nd.distance_transform_edt(solid)
    band = np.clip(1 - dist / (6 * SCALE), 0, 1) * solid
    h = nd.gaussian_filter(np.minimum(dist, 6 * SCALE), 1.5)
    gy, gx = np.gradient(h)
    shade = (-gx - gy) / (np.hypot(gx, gy) + 1e-6)  # +1 faces the light
    hi = np.clip(shade, 0, 1) * band
    lo = np.clip(-shade, 0, 1) * band
    bevel = np.zeros((*a.shape, 4), np.uint8)
    bevel[..., :3] = np.where(hi[..., None] >= lo[..., None], 255, 0)
    bevel[..., 3] = (np.maximum(hi * 0.75, lo * 0.55) * a * 255).astype(np.uint8)
    Image.fromarray(bevel, "RGBA").save(f"assets/logos/{name}-bevel.png", optimize=True)
    print(name, size)
