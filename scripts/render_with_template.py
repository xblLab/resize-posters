"""
使用 HTML 模板在浏览器中渲染图片，并输出为 1080x1920 的图片。

基本流程：
1. 启动本地 HTTP 服务器
2. 使用 Playwright 打开浏览器
3. 加载 HTML 模板（通过 URL 参数传入图片的 HTTP 路径；输入会先复制到 .render_cache/ 避免超长 URL）
4. 等待渲染完成后截图
5. 输出 1080x1920 的图片
"""

from __future__ import annotations

import argparse
import http.server
import json
import shutil
import socketserver
import sys
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

TARGET_W = 1080
TARGET_H = 1920
SKILL_ROOT = Path(__file__).parent.parent.resolve()
TEMPLATE_DIR = SKILL_ROOT / "templates"
DEFAULT_TEMPLATE = "default.html"
# 静态资源根目录：需能访问 templates/ 与 assets/（如系列手机框模板）
HTTP_ROOT = SKILL_ROOT
RENDER_CACHE_DIR = SKILL_ROOT / ".render_cache"
REGISTRY_PATH = TEMPLATE_DIR / "registry.json"


def resolve_template_path(template_arg: str) -> str:
    """将 -t 参数解析为 templates/ 下的相对路径。纯数字时查 registry.json。"""
    s = template_arg.strip()
    if s.isdigit():
        if not REGISTRY_PATH.is_file():
            print(f"模板编号已指定但缺少注册表: {REGISTRY_PATH}", file=sys.stderr)
            sys.exit(1)
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        tid = int(s)
        for item in data.get("templates", []):
            if item.get("id") == tid:
                return str(item["path"])
        print(f"未知模板编号: {tid}（请检查 templates/registry.json）", file=sys.stderr)
        sys.exit(1)
    return s


class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """支持 CORS 的 HTTP 请求处理器"""

    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=str(directory), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # 静默日志
        pass


def start_server(directory: Path, port: int = 0) -> tuple[int, socketserver.TCPServer]:
    """启动本地 HTTP 服务器，返回实际端口和服务器实例"""
    handler = lambda *args, **kwargs: CORSHTTPRequestHandler(*args, directory=directory, **kwargs)
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    actual_port = server.server_address[1]

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    return actual_port, server


def copy_image_to_serve_path(image_path: Path) -> str:
    """复制输入图到 HTTP 根下短路径，避免 base64 塞进 URL 导致 414。"""
    RENDER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    suffix = image_path.suffix.lower() or ".jpg"
    dest = RENDER_CACHE_DIR / f"{uuid.uuid4().hex}{suffix}"
    shutil.copy2(image_path, dest)
    rel = dest.relative_to(SKILL_ROOT)
    return "/" + rel.as_posix()


def render_with_playwright(
    image_path: Path,
    template_name: str,
    output_path: Path,
    server_port: int,
    title: str = "",
    subtitle: str = "",
    bg: str = "",
    title_color: str = "",
) -> None:
    """使用 Playwright 渲染页面并截图"""

    template_file = TEMPLATE_DIR / template_name
    if not template_file.exists():
        print(f"模板不存在: {template_file}", file=sys.stderr)
        sys.exit(1)

    # 构建 URL 参数（短路径，同机 HTTP 提供文件，避免超长 data URL 触发 414）
    image_serve_path = copy_image_to_serve_path(image_path)
    params = f"image={quote(image_serve_path, safe='/')}"
    if title:
        params += f"&title={quote(title)}"
    if subtitle:
        params += f"&subtitle={quote(subtitle)}"
    if bg:
        params += f"&bg={quote(bg)}"
    if title_color:
        params += f"&titleColor={quote(title_color)}"

    url = f"http://127.0.0.1:{server_port}/templates/{template_name}?{params}"

    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": TARGET_W, "height": TARGET_H},
            device_scale_factor=1,
        )
        page = context.new_page()

        # 导航到页面
        page.goto(url, wait_until="networkidle")

        # 等待图片加载完成
        try:
            page.wait_for_function(
                "() => window.__IMAGE_LOADED__ === true",
                timeout=10000
            )
        except Exception:
            print("警告: 图片加载超时，继续截图", file=sys.stderr)

        # 额外等待一下确保渲染完成
        time.sleep(0.5)

        # 截图
        output_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(
            path=str(output_path),
            type="jpeg",
            quality=95,
            full_page=False,
        )

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="使用 HTML 模板在浏览器中渲染图片并输出 1080x1920 图片"
    )
    parser.add_argument(
        "-i",
        "--image",
        type=Path,
        required=True,
        help="输入图片路径",
    )
    parser.add_argument(
        "-t",
        "--template",
        type=str,
        default=DEFAULT_TEMPLATE,
        help=(
            f"模板：相对 templates/ 的文件名（如 series_phone.html、pure-color/01.html），"
            f"或 registry 中的数字编号 1–40（见 templates/registry.json）（默认: {DEFAULT_TEMPLATE}）"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="输出图片路径（默认: output/<输入图片名>_rendered.jpg）",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="图片标题",
        help="模板中的标题文字",
    )
    parser.add_argument(
        "--subtitle",
        type=str,
        default="这里是副标题描述文字",
        help="模板中的副标题文字",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="本地服务器端口（默认: 8765，0 表示随机端口）",
    )
    parser.add_argument(
        "--bg",
        type=str,
        default="",
        help="背景色（十六进制，如 #1a1a2e；覆盖模板预设；纯色系列模板见 registry）",
    )
    parser.add_argument(
        "--title-color",
        type=str,
        default="",
        dest="title_color",
        help="标题颜色（十六进制，如 #f5f5f7；不传则由模板根据背景亮度自动决定）",
    )
    args = parser.parse_args()

    image_path = args.image.resolve()
    if not image_path.is_file():
        print(f"图片不存在: {image_path}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = args.output.resolve()
    else:
        output_dir = Path("output").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{image_path.stem}_rendered.jpg"

    # 启动服务器（根目录为 skill 根，便于模板引用 /assets/）
    print(f"启动本地服务器...")
    port, server = start_server(HTTP_ROOT, args.port)
    print(f"服务器运行在 http://127.0.0.1:{port}")

    template_name = resolve_template_path(args.template)

    try:
        print(f"正在渲染: {image_path.name}（模板: {template_name}）")
        render_with_playwright(
            image_path=image_path,
            template_name=template_name,
            output_path=output_path,
            server_port=port,
            title=args.title,
            subtitle=args.subtitle,
            bg=args.bg,
            title_color=args.title_color,
        )
        print(f"渲染完成: {output_path}")
    finally:
        server.shutdown()
        print("服务器已关闭")


if __name__ == "__main__":
    main()
