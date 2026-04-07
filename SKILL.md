---
name: resize-posts-1080x1920
description: |
  批量把目录里的图片统一成 1080×1920 竖版：等比放大做 cover（可能裁左右或底部）、水平居中、顶对齐保上方内容；支持 png/jpg/jpeg/webp/bmp，RGBA 先铺白再输出 JPEG。只要用户提到整目录素材、posts 出图、上架/应用商店竖版海报、Story 竖图、1080×1920、9:16、竖屏封面、批量缩放且接受裁切（尤其保顶）——即使没说脚本名——就应使用本 skill 并执行 bundled 脚本，而不是用 Pillow 手写一遍或猜尺寸。不要用本 skill：只要「放进画布里不裁切」的 fit/letterbox、只压缩体积（如 TinyPNG API）、不要改分辨率、只要单张交互裁图、或需要递归处理所有子文件夹（当前脚本只处理输入目录直接子文件）。
---

# 目录图片 → 1080×1920（顶对齐 cover）

## 行为摘要

- 每张图等比缩放直至完全盖住 1080×1920，再居中水平裁切、从顶部对齐（**底部多余被裁掉**）。
- **仅处理输入目录下一层**中的图片，**不递归**子目录。若素材在子文件夹里，对每层分别 `-i`，或先说明需改脚本再实现递归。

## 运行方式

脚本路径（相对本 skill 根目录）：`scripts/resize_posts_1080x1920.py`。

在终端执行（将 `<SKILL_ROOT>` 换成本 skill 目录的绝对路径，`<IN>` 换成输入目录）：

```bash
python3 <SKILL_ROOT>/scripts/resize_posts_1080x1920.py -i <IN>
```

可选输出目录（默认 `<IN>/out_1080x1920`）：

```bash
python3 <SKILL_ROOT>/scripts/resize_posts_1080x1920.py -i <IN> -o <OUT_DIR>
```

**依赖**：需要 Pillow。若失败提示没有 PIL，可 `pip install pillow`，或在工作区已配置 `uv`/`pyproject.toml` 且含 pillow 时在该工作区用 `uv run python <SKILL_ROOT>/scripts/resize_posts_1080x1920.py ...`。

## 完成后告知用户

- 输出目录路径（默认或自定义）。
- 处理了多少文件。

## 与仓库副本

同一逻辑可能存在于用户项目中的 `resize_posts_1080x1920.py`；以本 skill 内 `scripts/` 为准执行即可，行为一致。
