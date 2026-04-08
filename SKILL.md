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

若工作区使用 **uv**（已有 `pyproject.toml` / `uv.lock`，或在本目录已 `uv venv` 并装好 Pillow），可将上述命令里的 `python3` 换成 `uv run python`，以固定使用项目虚拟环境，例如：

```bash
uv run python <SKILL_ROOT>/scripts/resize_posts_1080x1920.py -i <IN> -o <OUT_DIR>
```

**依赖**：Pillow。缺失时 `pip install pillow`，或用 uv 在对应环境中安装后再执行。

## 完成后告知用户

- 输出目录路径（默认或自定义）。
- 处理了多少文件。

## 与仓库副本

同一逻辑可能存在于用户项目中的 `resize_posts_1080x1920.py`；以本 skill 内 `scripts/` 为准执行即可，行为一致。

---

# HTML 模板渲染（实验性功能）

除了直接缩放图片，本 skill 还支持将图片传入 HTML 模板，在浏览器中渲染后截图输出 1080×1920 图片。

## 行为摘要

1. 启动本地 HTTP 服务器
2. 使用 Playwright 打开 Chromium 浏览器
3. 加载 HTML 模板（通过 URL 参数传入图片、标题等数据）
4. 等待渲染完成后截图
5. 输出 1080×1920 JPEG 图片

## 运行方式

脚本路径：`scripts/render_with_template.py`

基础用法：

```bash
python3 scripts/render_with_template.py -i <图片路径> --title "标题" --subtitle "副标题"
```

完整参数：

```bash
python3 scripts/render_with_template.py \
  -i input.jpg \
  -t default.html \
  -o output.jpg \
  --title "图片标题" \
  --subtitle "副标题描述" \
  --port 8765
```

使用 uv 时同上：将 `python3` 换为 `uv run python` 即可。

参数说明：

- `-i, --image`: 输入图片路径（必需）
- `-t, --template`: 模板文件名，默认 `default.html`
- `-o, --output`: 输出图片路径，默认 `output/<输入图片名>_rendered.jpg`
- `--title`: 模板中的标题文字
- `--subtitle`: 模板中的副标题文字
- `--port`: 本地服务器端口，默认 8765

## 模板系统

模板存放在 `templates/` 目录，是标准 HTML 文件。

**模板数据传递方式**：通过 URL 查询参数传递

- `image`: 图片的 base64 data URL（自动编码）
- `title`: 标题文字
- `subtitle`: 副标题文字

**示例模板结构** (`templates/default.html`)：

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080, initial-scale=1.0">
  <style>
    body {
      width: 1080px;
      height: 1920px;
      /* 你的样式 */
    }
  </style>
</head>
<body>
  <img id="target-image" src="">
  <div id="title-text"></div>
  <div id="subtitle-text"></div>

  <script>
    // 从 URL 参数获取数据
    const params = new URLSearchParams(window.location.search);
    document.getElementById('target-image').src = params.get('image');
    document.getElementById('title-text').textContent = params.get('title');
    document.getElementById('subtitle-text').textContent = params.get('subtitle');

    // 图片加载完成后通知
    document.getElementById('target-image').onload = function() {
      window.__IMAGE_LOADED__ = true;
    };
  </script>
</body>
</html>
```

**模板开发规范**：

1. 页面尺寸必须设置为 `1080px × 1920px`
2. 图片通过 `window.location.search` 获取 `image` 参数
3. 可选：在图片 `onload` 事件中设置 `window.__IMAGE_LOADED__ = true`，脚本会等待此信号
4. 模板可自定义任意样式和布局

## 依赖安装

HTML 模板渲染需要 Playwright 和 Chromium：

```bash
# 使用 uv（推荐；在 skill 根目录或你的项目根目录执行）
uv venv
uv pip install playwright pillow
uv run python -m playwright install chromium

# 或使用 pip + 系统/当前环境的 python3
pip install playwright pillow
python3 -m playwright install chromium
```

## 示例

```bash
# 基础渲染（uv：把 python3 换成 uv run python）
python3 scripts/render_with_template.py -i photo.jpg --title "精选照片"

# 完整参数
python3 scripts/render_with_template.py \
  -i ~/Downloads/photo.jpg \
  -t default.html \
  -o ~/Desktop/poster.jpg \
  --title "旅行日记" \
  --subtitle "记录美好时光"
```
