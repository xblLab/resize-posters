#!/usr/bin/env python3
"""在 skill 根目录检测并补齐 HTML 模板渲染依赖：先检测再装；优先 uv sync，否则使用 .venv + pip。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_CHECK = r"""
import sys
from pathlib import Path
try:
    import PIL  # noqa: F401
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit(1)
try:
    with sync_playwright() as p:
        ep = p.chromium.executable_path
        if ep and Path(ep).is_file():
            sys.exit(0)
except Exception:
    pass
sys.exit(2)
"""


def _venv_python() -> Path:
    venv = ROOT / ".venv"
    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.check_call(cmd, cwd=ROOT)


def _status(py: list[str]) -> int:
    """0: 就绪；1: 缺 Python 包；2: 仅缺 Chromium。"""
    p = subprocess.run(
        py + ["-c", _CHECK],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return p.returncode


def _python_stdlib_ok(py: Path) -> bool:
    try:
        subprocess.run(
            [str(py), "-c", "import encodings"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            timeout=20,
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _ensure_venv_no_uv() -> list[str]:
    vdir = ROOT / ".venv"
    py = _venv_python()
    if py.is_file() and not _python_stdlib_ok(py):
        shutil.rmtree(vdir, ignore_errors=True)
        py = _venv_python()
    if not py.is_file():
        _run([sys.executable, "-m", "venv", str(vdir)])
        py = _venv_python()
    return [str(py)]


def main() -> int:
    os.chdir(ROOT)
    uv = shutil.which("uv")
    use_uv = bool(uv and (ROOT / "pyproject.toml").is_file())

    if use_uv:
        if _status([uv, "run", "python"]) == 0:
            print("OK: Pillow + Playwright + Chromium 已就绪", file=sys.stderr)
            return 0
        _run([uv, "sync"])
        py = [uv, "run", "python"]
    else:
        py = _ensure_venv_no_uv()

    st = _status(py)
    if st == 1:
        if use_uv:
            _run([uv, "sync"])
        else:
            _run(py + ["-m", "pip", "install", "-q", "pillow", "playwright"])
        st = _status(py)

    if st == 1:
        print("仍无法 import Pillow/Playwright。", file=sys.stderr)
        return 1

    if st == 2:
        _run(py + ["-m", "playwright", "install", "chromium"])
        st = _status(py)

    if st != 0:
        print("Chromium 未就绪（playwright install 可能失败）。", file=sys.stderr)
        return 1

    print("OK: Pillow + Playwright + Chromium 已就绪", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
