"""
在 skill 根目录启动静态 HTTP，打印模板画廊 URL（与 render_with_template 使用同一 HTTP 根）。

不依赖 Playwright，仅用于浏览器预览 templates/gallery.html。
"""

from __future__ import annotations

import argparse
import http.server
import socketserver
import threading
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
HTTP_ROOT = SKILL_ROOT


class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """与 render_with_template 一致：CORS + 静默日志。"""

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
        pass


def start_server(directory: Path, port: int = 0) -> tuple[int, socketserver.TCPServer]:
    handler = lambda *args, **kwargs: CORSHTTPRequestHandler(*args, directory=directory, **kwargs)
    server = socketserver.TCPServer(("127.0.0.1", port), handler)
    actual_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return actual_port, server


def main() -> None:
    parser = argparse.ArgumentParser(description="启动本地 HTTP，打开模板画廊预览页")
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="端口（默认 8765；0 表示随机）",
    )
    args = parser.parse_args()

    port, server = start_server(HTTP_ROOT, args.port)
    gallery = f"http://127.0.0.1:{port}/templates/gallery.html"
    print(f"画廊: {gallery}")
    print("按 Ctrl+C 结束")
    try:
        import time

        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        print("已关闭")


if __name__ == "__main__":
    main()
