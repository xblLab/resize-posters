---
name: resize-posts-1080x1920
description: |
  批量把目录里的图片统一成 1080×1920 竖版：等比放大做 cover（可能裁左右或底部）、水平居中、顶对齐保上方内容；支持 png/jpg/jpeg/webp/bmp，RGBA 先铺白再输出 JPEG。只要用户提到整目录素材、posts 出图、上架/应用商店竖版海报、Story 竖图、1080×1920、9:16、竖屏封面、批量缩放且接受裁切（尤其保顶）——即使没说脚本名——就应使用本 skill 并执行 bundled 脚本，而不是用 Pillow 手写一遍或猜尺寸。不要用本 skill：只要「放进画布里不裁切」的 fit/letterbox、只压缩体积（如 TinyPNG API）、不要改分辨率、只要单张交互裁图、或需要递归处理所有子文件夹（当前脚本只处理输入目录直接子文件）。
  HTML 模板出图（`scripts/render_with_template.py`）：上架纯色+机框可用 `-t` 传数字选预设（`1`–`5` 浅色 `pure-color`，`6`–`10` 中深 `pure-color-dark`、默认白字，`11`–`15` 浅色模糊渐变 `blur-gradient-light`，`16`–`20` 深色模糊渐变 `blur-gradient-dark`，`21`–`25` 浅色 `abstract-shape-light`（color4bg Abstract Shape），`26`–`30` 深色 `abstract-shape-dark`，`31`–`35` 浅色 `grid-array-light`（color4bg Grid Array），`36`–`40` 深色 `grid-array-dark`，`41`–`45` 浅色 `triangles-mosaic-light`（color4bg TrianglesMosaic），`46`–`50` 深色 `triangles-mosaic-dark`，`51`–`55` 浅色 `linear-gradient-light`，`56`–`60` 深色 `linear-gradient-dark`，`61`–`62` 双屏连贯 `store_pair_left` / `store_pair_right`；登记在 `templates/registry.json`），亦可用路径如 `pure-color-dark/02.html`、`linear-gradient-light/01.html`；可选 `--bg`、`--title-color` 覆盖预设；双屏一键出图可用 `--pair`。渲染前须先跑 `scripts/ensure_render_deps.py`（先检测再装，优先 uv，见正文「依赖安装」）。
  模板组（`templates/template_groups.json`，每组 1–5 个 registry 编号）：`scripts/render_template_group.py -g <组id>` 按组内顺序依次出图；`-i` 可为单图或**一层目录**（批量），输出 `<stem>_g<组id>_t<模板号>.jpg`；`--list-groups` 列出全部组。
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

**依赖**：Pillow。缺失时 `pip install pillow`，或在本 skill 根目录 `uv sync`（见 `pyproject.toml`）。若需 **HTML 模板渲染**（Playwright），请先执行 `scripts/ensure_render_deps.py`（先检测再装，见下文「依赖安装」）。

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

使用 uv 时：先在本 skill 根目录执行 `uv run python scripts/ensure_render_deps.py`，再将下文命令中的 `python3` 换为 `uv run python`。

### 模板组批量出图（`scripts/render_template_group.py`）

`templates/template_groups.json` 定义多组（每组含 1–5 个 registry 编号）。`scripts/render_template_group.py -i <图或目录> -g <组id>` 在单次本地 HTTP 服务下渲染：对目录则**仅一层**批量处理（与缩放脚本相同后缀）；每张图按组内模板顺序各出一张，输出 `<stem>_g<组id>_t<模板号>.jpg`（默认目录 `output/`）；`-o` 传目录则写入该目录，传单文件路径仅在与**单张** `-i` 联用时作为输出文件名基准；`--list-groups` 列出全部组（无需 Playwright）。

```bash
python3 scripts/render_template_group.py -i photo.jpg -g 1 --title "标题"
python3 scripts/render_template_group.py -i assets/screenshots/demo-app -g 1 --title "标题" -o output/demo-app/
```

### 预览所有模板（浏览器）

`templates/gallery.html` 会读取 `templates/registry.json`，网格展示各编号模板（缩放 iframe）。**须通过 HTTP 访问**，勿用 `file://` 直接打开。

在本 skill **根目录**任选一种方式：

```bash
# 方式 A：一键起服务并打印画廊地址（无 Playwright 依赖）
python3 scripts/preview_gallery.py
# 可选：python3 scripts/preview_gallery.py --port 9000
```

```bash
# 方式 B：标准库静态服务
python3 -m http.server 8765
```

浏览器打开：`http://127.0.0.1:<端口>/templates/gallery.html`（`preview_gallery.py` 默认端口 8765 时即 `http://127.0.0.1:8765/templates/gallery.html`）。

**双屏模板并排调试**：单独打开 `store_pair_left` / `store_pair_right` 只能看到半边。可起同一 HTTP 后打开 `templates/preview_store_pair.html`，用两个 iframe 同时加载左右模板并同步截图与标题参数，改 CSS 后点「刷新两屏」即可对照拼接缝与整体构图（勿用 `file://`）。

参数说明：

- `-i, --image`: 输入图片路径（必需）
- `-t, --template`: 模板。可为 `templates/` 下相对路径（如 `series_phone.html`、`pure-color/03.html`、`linear-gradient-light/01.html`），或 **registry 中的数字编号**（见下表与 `templates/registry.json`）。默认 `default.html`
- `-o, --output`: 输出图片路径，默认 `output/<输入图片名>_rendered.jpg`
- `--title`: 模板中的标题文字
- `--subtitle`: 模板中的副标题文字
- `--bg`: 背景色（如 `#0d0d12`），覆盖模板预设；纯色系列不传则用该编号默认色
- `--title-color`: 标题颜色（如 `#f5f5f7`）；不传则由模板按背景亮度自动选深/浅字
- `--port`: 本地服务器端口，默认 8765
- `--pair`: 一次生成双屏连贯上架图（固定使用 `store_pair_left.html` 与 `store_pair_right.html`），输出 `<名>_pair_left` 与 `<名>_pair_right`（与 `-o` 同目录、同扩展名）；与 `-t` 互斥（指定 `--pair` 时忽略 `-t`）
- `--title-right`: 与 `--pair` 联用，右屏标题（默认与 `--title` 相同）

### 模板编号表（纯色 + 手机框，`pure-color/01.html`–`05.html`）

色相拉开（蓝 / 暖黄 / 绿 / 粉 / 紫），避免近邻套色糊成一片。

| 编号 | 文件 | 预设背景 | 说明 |
|------|------|----------|------|
| 1 | `pure-color/01.html` | `#E3F2FD` | 冰蓝 |
| 2 | `pure-color/02.html` | `#FFF8E6` | 蜜杏 |
| 3 | `pure-color/03.html` | `#E8F5E9` | 薄荷绿 |
| 4 | `pure-color/04.html` | `#FCE4EC` | 蔷薇粉 |
| 5 | `pure-color/05.html` | `#EDE7F6` | 丁香紫 |

### 模板编号表（中深色 + 白字默认，`pure-color-dark/01.html`–`05.html`）

色相拉开（蓝 / 红 / 绿 / 紫 / 棕）；默认标题为白色，`--bg` 改为浅色时会自动切深色字。

| 编号 | 文件 | 预设背景 | 说明 |
|------|------|----------|------|
| 6 | `pure-color-dark/01.html` | `#1B4A6B` | 钢蓝 |
| 7 | `pure-color-dark/02.html` | `#6B2D3C` | 酒红 |
| 8 | `pure-color-dark/03.html` | `#1F4D3A` | 松绿 |
| 9 | `pure-color-dark/04.html` | `#4A2D6B` | 茄紫 |
| 10 | `pure-color-dark/05.html` | `#6B4A2A` | 古铜 |

### 模板编号表（浅色模糊渐变 + 手机框，`blur-gradient-light/01.html`–`05.html`）

三层大色块 + `filter: blur`，底为浅色；默认标题深色字，`--bg` 为深色 hex 时会自动切白字。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|-------------|------|
| 11 | `blur-gradient-light/01.html` | `#EEF0F8` | 雾紫蓝渐变 |
| 12 | `blur-gradient-light/02.html` | `#F0F7F3` | 薄荷杏渐变 |
| 13 | `blur-gradient-light/03.html` | `#F2F8FF` | 晴空渐变 |
| 14 | `blur-gradient-light/04.html` | `#FBF5F8` | 蔷薇渐变 |
| 15 | `blur-gradient-light/05.html` | `#F5FBFC` | 青柠渐变 |

### 模板编号表（深色模糊渐变 + 手机框，`blur-gradient-dark/01.html`–`05.html`）

深色底 + 高饱和色块经强模糊叠色；默认标题白字。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|-------------|------|
| 16 | `blur-gradient-dark/01.html` | `#12141E` | 夜蓝紫渐变 |
| 17 | `blur-gradient-dark/02.html` | `#0D1612` | 森绿渐变 |
| 18 | `blur-gradient-dark/03.html` | `#141016` | 酒红渐变 |
| 19 | `blur-gradient-dark/04.html` | `#0A0E18` | 靛青渐变 |
| 20 | `blur-gradient-dark/05.html` | `#131210` | 琥珀渐变 |

### 模板编号表（浅色 Abstract Shape + 手机框，`abstract-shape-light/01.html`–`05.html`）

背景由 [color4bg](https://github.com/winterx/color4bg.js) 的 `AbstractShapeBg`（`loop: false`），本地脚本为 `assets/vendor/color4bg/AbstractShapeBg.min.js`；默认标题深色字，`--bg` 为深色 hex 时会自动切白字。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|-------------|------|
| 21 | `abstract-shape-light/01.html` | `#EEF4FF` | 冰雾抽象形 |
| 22 | `abstract-shape-light/02.html` | `#FFF6ED` | 蜜杏抽象形 |
| 23 | `abstract-shape-light/03.html` | `#EEF8F2` | 薄荷抽象形 |
| 24 | `abstract-shape-light/04.html` | `#FFF0F5` | 蔷薇抽象形 |
| 25 | `abstract-shape-light/05.html` | `#F3EEFE` | 丁香抽象形 |

### 模板编号表（深色 Abstract Shape + 手机框，`abstract-shape-dark/01.html`–`05.html`）

同上；默认标题白字。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|-------------|------|
| 26 | `abstract-shape-dark/01.html` | `#0C1424` | 深海抽象形 |
| 27 | `abstract-shape-dark/02.html` | `#140C18` | 酒红抽象形 |
| 28 | `abstract-shape-dark/03.html` | `#081210` | 墨绿抽象形 |
| 29 | `abstract-shape-dark/04.html` | `#0E0818` | 午夜抽象形 |
| 30 | `abstract-shape-dark/05.html` | `#121008` | 琥珀抽象形 |

### 模板编号表（浅色 Grid Array + 手机框，`grid-array-light/01.html`–`05.html`）

背景由 [color4bg](https://github.com/winterx/color4bg.js) 的 `GridArrayBg`（`loop: false`），本地脚本为 `assets/vendor/color4bg/GridArrayBg.min.js`；配色与编号 21–25 一一对应，默认标题深色字。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|-------------|------|
| 31 | `grid-array-light/01.html` | `#EEF4FF` | 冰雾网格 |
| 32 | `grid-array-light/02.html` | `#FFF6ED` | 蜜杏网格 |
| 33 | `grid-array-light/03.html` | `#EEF8F2` | 薄荷网格 |
| 34 | `grid-array-light/04.html` | `#FFF0F5` | 蔷薇网格 |
| 35 | `grid-array-light/05.html` | `#F3EEFE` | 丁香网格 |

### 模板编号表（深色 Grid Array + 手机框，`grid-array-dark/01.html`–`05.html`）

首色为暗底、其余为高明度强调色以拉开格线对比；实例化后对 `GridArrayBg` 调用 `update('borderwidth', 0.026)`、`update('scale', 104)`、`update('amplitude', 0.78)` 控制线宽与格网密度。默认标题白字。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|-------------|------|
| 36 | `grid-array-dark/01.html` | `#0C1424` | 深海网格 |
| 37 | `grid-array-dark/02.html` | `#140C18` | 酒红网格 |
| 38 | `grid-array-dark/03.html` | `#081210` | 墨绿网格 |
| 39 | `grid-array-dark/04.html` | `#0E0818` | 午夜网格 |
| 40 | `grid-array-dark/05.html` | `#121008` | 琥珀网格 |

### 模板编号表（浅色 Triangles Mosaic + 手机框，`triangles-mosaic-light/01.html`–`05.html`）

背景由 [color4bg](https://github.com/winterx/color4bg.js) 的 `TrianglesMosaicBg`（`loop: false`），本地脚本为 `assets/vendor/color4bg/TrianglesMosaicBg.min.js`；配色与编号 31–35 同系，默认标题深色字。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|-------------|------|
| 41 | `triangles-mosaic-light/01.html` | `#EEF4FF` | 冰雾三角拼 |
| 42 | `triangles-mosaic-light/02.html` | `#FFF6ED` | 蜜杏三角拼 |
| 43 | `triangles-mosaic-light/03.html` | `#EEF8F2` | 薄荷三角拼 |
| 44 | `triangles-mosaic-light/04.html` | `#FFF0F5` | 蔷薇三角拼 |
| 45 | `triangles-mosaic-light/05.html` | `#F3EEFE` | 丁香三角拼 |

### 模板编号表（深色 Triangles Mosaic + 手机框，`triangles-mosaic-dark/01.html`–`05.html`）

配色与编号 36–40 同系；默认标题白字。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|-------------|------|
| 46 | `triangles-mosaic-dark/01.html` | `#0C1424` | 深海三角拼 |
| 47 | `triangles-mosaic-dark/02.html` | `#140C18` | 酒红三角拼 |
| 48 | `triangles-mosaic-dark/03.html` | `#081210` | 墨绿三角拼 |
| 49 | `triangles-mosaic-dark/04.html` | `#0E0818` | 午夜三角拼 |
| 50 | `triangles-mosaic-dark/05.html` | `#121008` | 琥珀三角拼 |

### 模板编号表（浅色 CSS 线性渐变 + 手机框，`linear-gradient-light/01.html`–`05.html`）

纯 `linear-gradient`；默认深色标题；传 URL `bg` 时改为纯色底（与 `pure-color` 系列一致）。

| 编号 | 文件 | 预设 `--bg`（亮度参考） | 说明 |
|------|------|------------------------|------|
| 51 | `linear-gradient-light/01.html` | `#FFDAB9` | 晨曦 |
| 52 | `linear-gradient-light/02.html` | `#B8D4E8` | 冰川 |
| 53 | `linear-gradient-light/03.html` | `#E8D5F2` | 丁香 |
| 54 | `linear-gradient-light/04.html` | `#C8E6C9` | 春芽 |
| 55 | `linear-gradient-light/05.html` | `#FFCDD2` | 珊瑚 |

### 模板编号表（深色 CSS 线性渐变 + 手机框，`linear-gradient-dark/01.html`–`05.html`）

默认浅色标题；传 URL `bg` 为浅色 hex 时自动切深色字。

| 编号 | 文件 | 预设 `--bg`（亮度参考） | 说明 |
|------|------|------------------------|------|
| 56 | `linear-gradient-dark/01.html` | `#161B22` | 午夜 |
| 57 | `linear-gradient-dark/02.html` | `#1A2F4A` | 深海 |
| 58 | `linear-gradient-dark/03.html` | `#3D1428` | 酒韵 |
| 59 | `linear-gradient-dark/04.html` | `#0D3D3A` | 松涛 |
| 60 | `linear-gradient-dark/05.html` | `#2D1B4E` | 夜紫 |

### 模板编号表（双屏连贯 + 倾斜机框，`store_pair_left.html` / `store_pair_right.html`）

同一截图、同一套 3D 倾斜参数，虚拟舞台宽 2160px，左右各裁 1080×1920，拼合后机框与星空在接缝处连续；左屏顶左标题+副标题，右屏顶中标题。也可用 **`--pair`** 一次输出两张（见下文参数）。编号默认带 `url_params`（透视与旋转），可用 URL 或 CLI 覆盖。

| 编号 | 文件 | 预设 `--bg` | 说明 |
|------|------|---------------|------|
| 61 | `store_pair_left.html` | `#0a1228` | 双屏左 |
| 62 | `store_pair_right.html` | `#0a1228` | 双屏右 |

权威数据与后续扩展：`templates/registry.json`。

## 模板系统

模板存放在 `templates/` 目录，是标准 HTML 文件。内置示例：`default.html`（大图+底部标题）；`series_phone.html` 与 `pure-color/`、`pure-color-dark/`（纯色底）、`linear-gradient-light/`、`linear-gradient-dark/`（CSS 线性渐变底）、`blur-gradient-light/`、`blur-gradient-dark/`（模糊渐变底）、`abstract-shape-light/`、`abstract-shape-dark/`（color4bg Abstract Shape）、`grid-array-light/`、`grid-array-dark/`（color4bg Grid Array）、`triangles-mosaic-light/`、`triangles-mosaic-dark/`（color4bg TrianglesMosaic）；`store_pair_left.html` / `store_pair_right.html` 为双屏连贯星夜底+倾斜机框（见上表）。多数为顶部标题、中间 `assets/devices/mate70pro/Mate70-Pro.png` 机框；编号与 `registry.json` 一致。

**模板数据传递方式**：通过 URL 查询参数传递

- `image`: 输入图在本地 HTTP 下的路径（脚本会将 `-i` 复制到 `.render_cache/` 再传入，避免超长 URL 导致 414）
- `title`: 标题文字
- `subtitle`: 副标题文字
- `bg`（可选）：背景色，如 `#1a1a2e`（多数模板作纯色底；`linear-gradient-*` 模板在传入时覆盖为纯色，不传则保留该文件内建渐变）
- `titleColor` 或 `title_color`（可选）：标题色；不传则浅色背景时自动用深色字（与 CLI `--title-color` 对应）
- `subtitleColor` 或 `subtitle_color`（可选，仅 `store_pair_left`）：副标题色
- `rotateZ` / `rotateY` / `rotateX`（可选，度；可带或不带 `deg`）：倾斜机框 3D 旋转，默认约 `22` / `-12` / `6`
- `perspective`（可选）：透视距离，默认 `2200`（可写 `2200` 或 `2200px`）

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
    document.getElementById('target-image').src = params.get('image') || '';
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

HTML 模板渲染需要 Pillow、Playwright 与 Chromium。请使用 **`scripts/ensure_render_deps.py`**：先检测（import + Chromium 可执行文件），**仅在缺失时**再执行 `uv sync` 或 `playwright install chromium`；已全部就绪时不会重复安装。

在 **skill 根目录**（与 `pyproject.toml` 同级）执行：

```bash
# 推荐：已安装 uv 时（优先读 pyproject.toml / uv.lock）
uv run python scripts/ensure_render_deps.py
```

未安装 `uv` 时，脚本会在本目录创建 `.venv` 并在检测失败时用 `pip` 补齐：

```bash
python3 scripts/ensure_render_deps.py
```

通过后，请用 **与检测一致** 的解释器跑渲染脚本，例如：

```bash
uv run python scripts/render_with_template.py -i photo.jpg --title "精选照片"
```

**说明**：自动化助手执行本 skill 时，应先跑 `ensure_render_deps.py` 再跑 `render_with_template.py`，不要无条件执行 `uv venv` + 全量 `pip install`。

**仅目录缩放**（`resize_posts_1080x1920.py`）只需 Pillow；若已有 `uv`，`uv sync` 即可，无需 Playwright。

## 示例

```bash
# 基础渲染（uv：把 python3 换成 uv run python）
python3 scripts/render_with_template.py -i photo.jpg --title "精选照片"

# 系列模板：纯色底 + 标题 + 手机框（`--bg` / `--title-color` 可选）
python3 scripts/render_with_template.py -i shot.jpg -t series_phone.html --title "功能亮点" --bg "#0d0d12" -o ~/Desktop/poster.jpg

# 线性渐变底 + 手机框（`-t 53` 等价于 `linear-gradient-light/03.html`）
python3 scripts/render_with_template.py -i shot.jpg -t linear-gradient-light/03.html --title "功能亮点" -o ~/Desktop/poster_grad.jpg

# 按编号使用浅色预设（等价于 -t pure-color/03.html）
python3 scripts/render_with_template.py -i shot.jpg -t 3 --title "功能亮点" -o ~/Desktop/poster.jpg

# 按编号使用中深预设、默认白字（等价于 -t pure-color-dark/01.html）
python3 scripts/render_with_template.py -i shot.jpg -t 6 --title "功能亮点" -o ~/Desktop/poster_dark.jpg

# 完整参数
python3 scripts/render_with_template.py \
  -i ~/Downloads/photo.jpg \
  -t default.html \
  -o ~/Desktop/poster.jpg \
  --title "旅行日记" \
  --subtitle "记录美好时光"

# 双屏连贯（一次两张；副标题仅左屏）
python3 scripts/render_with_template.py \
  -i shot.jpg --pair \
  --title "每晚睡得更好" \
  --title-right "用舒缓声音放松" \
  --subtitle "睡眠故事、白噪音与冥想" \
  -o ~/Desktop/store.jpg

# 单独渲染双屏之一（等价于编号 61 / 62）
python3 scripts/render_with_template.py -i shot.jpg -t 61 --title "左屏标题" --subtitle "左屏副标题" -o ~/Desktop/left.jpg
python3 scripts/render_with_template.py -i shot.jpg -t 62 --title "右屏标题" -o ~/Desktop/right.jpg
```
