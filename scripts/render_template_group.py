"""
按模板组（templates/template_groups.json）批量渲染上架图：单次 HTTP，依次使用组内各 registry 编号。

依赖与 render_with_template.py 相同（Playwright）；运行前建议先执行 ensure_render_deps.py。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent.resolve()
TEMPLATE_GROUPS_PATH = SKILL_ROOT / "templates" / "template_groups.json"
REGISTRY_PATH = SKILL_ROOT / "templates" / "registry.json"
HTTP_ROOT = SKILL_ROOT

# 与 resize_posts_1080x1920.py 一致：目录输入只处理一层内的这些后缀
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp"})


def load_registry_template_ids() -> set[int]:
    if not REGISTRY_PATH.is_file():
        print(f"缺少注册表: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {int(item["id"]) for item in data.get("templates", []) if "id" in item}


def load_template_groups() -> dict:
    if not TEMPLATE_GROUPS_PATH.is_file():
        print(f"缺少模板组文件: {TEMPLATE_GROUPS_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(TEMPLATE_GROUPS_PATH.read_text(encoding="utf-8"))


def list_groups() -> None:
    data = load_template_groups()
    for g in data.get("groups", []):
        gid = g.get("id")
        name = g.get("name", "")
        tids = g.get("template_ids", [])
        print(f"id={gid}\tname={name}\ttemplate_ids={tids}")


def find_group(data: dict, group_id: int) -> dict:
    for g in data.get("groups", []):
        if g.get("id") == group_id:
            return g
    print(f"未知模板组 id: {group_id}（见 {TEMPLATE_GROUPS_PATH}）", file=sys.stderr)
    sys.exit(1)


def validate_group(group: dict, registry_ids: set[int]) -> list[int]:
    tids = group.get("template_ids")
    if not isinstance(tids, list) or len(tids) < 1:
        print("template_ids 必须为非空数组", file=sys.stderr)
        sys.exit(1)
    if len(tids) > 5:
        print("template_ids 最多 5 个", file=sys.stderr)
        sys.exit(1)
    out: list[int] = []
    for x in tids:
        if not isinstance(x, int):
            print(f"template_ids 元素必须为整数: {x!r}", file=sys.stderr)
            sys.exit(1)
        if x not in registry_ids:
            print(f"未知模板编号: {x}（请检查 templates/registry.json）", file=sys.stderr)
            sys.exit(1)
        out.append(x)
    return out


def collect_input_images(path: Path) -> list[Path]:
    """单文件或目录（仅一层，不递归）。"""
    if path.is_file():
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            print(f"不支持的图片格式: {path}", file=sys.stderr)
            sys.exit(1)
        return [path]
    if path.is_dir():
        files = [
            p
            for p in sorted(path.iterdir())
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
        ]
        if not files:
            print(f"目录中无支持的图片: {path}", file=sys.stderr)
            sys.exit(1)
        return files
    print(f"路径不存在: {path}", file=sys.stderr)
    sys.exit(1)


def is_output_dir_arg(p: Path) -> bool:
    """`-o` 表示输出目录：如 `out/demo/`、`out/demo`（非 .jpg 等扩展名）。"""
    s = str(p)
    if s.endswith(("/", "\\")):
        return True
    if p.exists() and p.is_dir():
        return True
    if p.suffix.lower() in IMAGE_SUFFIXES:
        return False
    return True


def output_path_for_slot(
    image_path: Path,
    output_arg: Path | None,
    group_id: int,
    template_id: int,
    *,
    num_inputs: int,
) -> Path:
    suffix = ".jpg"
    if output_arg is None:
        parent = Path("output").resolve()
        stem = image_path.stem
    elif is_output_dir_arg(output_arg):
        parent = output_arg.resolve()
        stem = image_path.stem
    else:
        if num_inputs > 1:
            print(
                "-o 为具体图片路径时仅支持单张输入；多张请传输出目录（如 -o output/demo/）或省略 -o",
                file=sys.stderr,
            )
            sys.exit(1)
        parent = output_arg.parent
        stem = output_arg.stem
        if output_arg.suffix:
            suffix = output_arg.suffix
    parent.mkdir(parents=True, exist_ok=True)
    return parent / f"{stem}_g{group_id}_t{template_id}{suffix}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="按模板组批量渲染 1080×1920 上架图（templates/template_groups.json）"
    )
    parser.add_argument(
        "--list-groups",
        action="store_true",
        help="列出全部模板组后退出",
    )
    parser.add_argument(
        "-i",
        "--image",
        type=Path,
        default=None,
        help="输入：单张图片路径，或含多张图片的目录（仅一层，不递归；png/jpg/jpeg/webp/bmp）",
    )
    parser.add_argument(
        "-g",
        "--group",
        type=int,
        default=None,
        dest="group_id",
        help="模板组 id（见 templates/template_groups.json）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=(
            "输出：默认目录 output/；传目录则写入该目录；传单文件路径（如 out/base.jpg）"
            "仅在与单张 -i 联用时作为文件名基准"
        ),
    )
    parser.add_argument("--title", type=str, default="图片标题")
    parser.add_argument("--subtitle", type=str, default="这里是副标题描述文字")
    parser.add_argument("--port", type=int, default=8765, help="本地服务器端口（0=随机）")
    parser.add_argument("--bg", type=str, default="")
    parser.add_argument("--title-color", type=str, default="", dest="title_color")
    args = parser.parse_args()

    if args.list_groups:
        list_groups()
        return

    from render_with_template import (
        resolve_template,
        render_with_playwright,
        start_server,
    )

    if args.image is None or args.group_id is None:
        parser.error("渲染时请同时指定 -i/--image 与 -g/--group，或使用 --list-groups")

    input_path = args.image.resolve()
    image_paths = collect_input_images(input_path)
    n = len(image_paths)

    registry_ids = load_registry_template_ids()
    data = load_template_groups()
    group = find_group(data, args.group_id)
    template_ids = validate_group(group, registry_ids)

    port, server = start_server(HTTP_ROOT, args.port)
    print(f"服务器运行在 http://127.0.0.1:{port}")
    print(f"输入 {n} 张图，模板组内 {len(template_ids)} 个模板，共 {n * len(template_ids)} 个输出文件")
    try:
        for image_path in image_paths:
            for tid in template_ids:
                template_name, registry_extra = resolve_template(str(tid))
                out_path = output_path_for_slot(
                    image_path,
                    args.output,
                    args.group_id,
                    tid,
                    num_inputs=n,
                )
                print(f"正在渲染: {image_path.name}（模板 {tid}）→ {out_path.name}")
                render_with_playwright(
                    image_path=image_path,
                    template_name=template_name,
                    output_path=out_path,
                    server_port=port,
                    title=args.title,
                    subtitle=args.subtitle,
                    bg=args.bg,
                    title_color=args.title_color,
                    extra_query=registry_extra,
                )
                print(f"完成: {out_path}")
    finally:
        server.shutdown()
        print("服务器已关闭")


if __name__ == "__main__":
    main()
