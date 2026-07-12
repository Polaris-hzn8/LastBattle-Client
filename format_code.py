#!/usr/bin/env python3
"""Format C# scripts with clang-format using repo .clang-format."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


FORMAT_DIRS = ("Assets",)
SOURCE_SUFFIXES = {".cs"}
SKIP_DIRS = ("protobuf-net", "ProtobuMsg", "NGUI", "Xeffect")


def fix_utf16_files(files: List[str]) -> None:
    """Convert UTF-16 LE encoded files to UTF-8 in-place."""
    for f in files:
        try:
            with open(f, "rb") as fh:
                head = fh.read(2)
            if head == b"\xff\xfe":
                with open(f, "r", encoding="utf-16-le") as fh:
                    content = fh.read()
                with open(f, "w", encoding="utf-8", newline="") as fh:
                    fh.write(content)
                print(f"converted to UTF-8: {f}")
        except Exception:
            pass

def collect_source_files(root: Path) -> List[str]:
    files: List[str] = []

    for relative_dir in FORMAT_DIRS:
        base_dir = root / relative_dir
        if not base_dir.is_dir():
            continue

        for current_root, dirnames, filenames in os.walk(base_dir):
            # Skip third-party or generated trees to avoid unrelated diffs.
            dirnames[:] = [dirname for dirname in dirnames if dirname not in SKIP_DIRS]

            for filename in filenames:
                file_path = Path(current_root) / filename
                if file_path.suffix in SOURCE_SUFFIXES:
                    files.append(str(file_path))

    files.sort()
    return files


def run_clang_format(clang_format: str, files: List[str], label: str) -> int:
    """Run clang-format on each file."""
    count = 0
    for f in files:
        try:
            subprocess.run([clang_format, "-i", "--style=file", f], check=True, capture_output=True)
            count += 1
        except subprocess.CalledProcessError as e:
            print(f"warning: {f}: {e.stderr.decode().strip()}", file=sys.stderr)
    print(f"formatted {count}/{len(files)} {label} file(s) with .clang-format")
    return count


def main() -> int:
    root = Path(__file__).resolve().parent
    clang_format = os.environ.get("CLANG_FORMAT", "clang-format")

    if shutil.which(clang_format) is None:
        print(
            f"error: '{clang_format}' not found. Install LLVM clang-format or set CLANG_FORMAT.",
            file=sys.stderr,
        )
        return 1

    files = collect_source_files(root)
    if not files:
        print(f"no source files matched under {' '.join(FORMAT_DIRS)}")
        return 0

    # 格式化 C# 文件
    cs_files = [f for f in files if f.endswith('.cs')]

    # Convert UTF-16 LE files to UTF-8 so clang-format can handle them
    fix_utf16_files(cs_files)

    formatted_count = 0
    
    if cs_files:
        formatted_count += run_clang_format(clang_format, cs_files, "C#")
    
    if formatted_count == 0:
        print(f"no source files matched under {' '.join(FORMAT_DIRS)}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())