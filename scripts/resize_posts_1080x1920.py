"""将目录内图片等比放大至填满 1080×1920，水平居中、顶对齐，裁掉底部多余区域。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

TARGET_W = 1080
TARGET_H = 1920
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp"})


def is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES


def cover_top_align(img: Image.Image) -> Image.Image:
    """等比缩放使画面完全覆盖 TARGET，取顶部区域（底部被裁）。"""
    iw, ih = img.size
    scale = max(TARGET_W / iw, TARGET_H / ih)
    nw = max(1, round(iw * scale))
    nh = max(1, round(ih * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - TARGET_W) // 2
    top = 0
    return resized.crop((left, top, left + TARGET_W, top + TARGET_H))


def process_one(src: Path, dst: Path) -> None:
    with Image.open(src) as im:
        im = im.convert("RGB") if im.mode not in ("RGB", "RGBA") else im
        if im.mode == "RGBA":
            background = Image.new("RGB", im.size, (255, 255, 255))
            background.paste(im, mask=im.split()[3])
            im = background
        out = cover_top_align(im)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, quality=92, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="图片 → 1080×1920（顶对齐 cover 裁底）")
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=Path("posts"),
        help="输入目录（默认：posts）",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="输出目录（默认：<输入目录>/out_1080x1920）",
    )
    args = parser.parse_args()
    in_dir = args.input_dir.resolve()
    if not in_dir.is_dir():
        print(f"输入目录不存在: {in_dir}", file=sys.stderr)
        sys.exit(1)
    out_dir = (args.output_dir or (in_dir / "out_1080x1920")).resolve()

    files = sorted(p for p in in_dir.iterdir() if is_image(p))
    if not files:
        print(f"{in_dir} 下没有支持的图片文件。", file=sys.stderr)
        sys.exit(1)

    for src in files:
        dst = out_dir / src.name
        process_one(src, dst)
        print(f"{src.name} → {dst}")


if __name__ == "__main__":
    main()
