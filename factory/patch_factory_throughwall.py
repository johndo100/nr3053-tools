#!/usr/bin/env python3
"""Patch a Viettel NR3053 Factory dump with the stock through-wall values."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path

FACTORY_SIZE = 0x200000
PATCH_VALUE = b"\xc4\xc4"

# Keep this list byte-for-byte equivalent to the verified stock shell script.
# Several offsets are intentionally odd, so the two-byte writes overlap.
WRITE_OFFSETS = (
    0x81E,
    0x81F,
    0x820,
    0x821,
    0x822,
    0x823,
    0x824,
    0x825,
    0x826,
    0x827,
    0x828,
    0x82C,
    0x82D,
    0x82E,
    0x82F,
    0x830,
    0x835,
    0x836,
    0x837,
    0x838,
    0x839,
    0x83E,
    0x83F,
    0x840,
    0x841,
    0x842,
    0x848,
    0x849,
    0x84A,
    0x84B,
    0x84C,
    0x852,
    0x853,
    0x854,
    0x855,
    0x856,
    0x85C,
    0x85D,
    0x85E,
    0x85F,
    0x860,
    0x866,
    0x867,
    0x868,
    0x869,
    0x86A,
    0x870,
    0x871,
    0x872,
    0x873,
    0x874,
    0x87A,
    0x87B,
    0x87C,
    0x87D,
    0x87E,
)
TARGET_BYTES = frozenset(
    byte_offset
    for write_offset in WRITE_OFFSETS
    for byte_offset in range(write_offset, write_offset + len(PATCH_VALUE))
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_factory(data: bytes) -> None:
    if len(data) != FACTORY_SIZE:
        raise ValueError(
            f"Factory phải đúng 0x{FACTORY_SIZE:x} byte "
            f"({FACTORY_SIZE} byte), nhận được 0x{len(data):x} byte"
        )
    if not any(byte != 0x00 for byte in data):
        raise ValueError("Factory toàn 0x00; từ chối patch")
    if not any(byte != 0xFF for byte in data):
        raise ValueError("Factory toàn 0xff; từ chối patch")


def patched_bytes(data: bytes) -> tuple[bytes, tuple[int, ...]]:
    validate_factory(data)
    patched = bytearray(data)
    for offset in WRITE_OFFSETS:
        patched[offset : offset + len(PATCH_VALUE)] = PATCH_VALUE

    result = bytes(patched)
    changed = tuple(
        offset
        for offset, (before, after) in enumerate(zip(data, result, strict=True))
        if before != after
    )
    unexpected = set(changed) - TARGET_BYTES
    if unexpected:
        raise RuntimeError("lỗi nội bộ: có byte ngoài vùng through-wall bị đổi")
    return result, changed


def default_output_path(input_path: Path) -> Path:
    # Keenetic U-Boot Flash Editor derives the MTD target and byte range from
    # this filename form.  Keeping it as the default prevents a valid Factory
    # image from being rejected by the Restore UI as an unknown backup.
    return input_path.with_name(
        f"{input_path.stem}.throughwall_mtd_Factory_0x0-0x{FACTORY_SIZE:x}.bin"
    )


def is_flash_editor_filename(path: Path) -> bool:
    """Return whether Keenetic U-Boot can derive the Factory restore range."""
    return f"_mtd_Factory_0x0-0x{FACTORY_SIZE:x}" in path.name


def write_private_atomic(path: Path, data: bytes, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output đã tồn tại: {path}; dùng --force để ghi đè")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        temporary.write(data)
        temporary.flush()
        os.fsync(temporary.fileno())
    try:
        temporary_path.chmod(0o600)
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Patch bản dump Factory 2 MiB của Viettel NR3053 bằng các giá trị "
            "through-wall 0xc4; không sửa file đầu vào."
        )
    )
    parser.add_argument("input", type=Path, help="file Factory gốc dump từ U-Boot")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "file Factory đã patch; tên phải chứa "
            "_mtd_Factory_0x0-0x200000 để Flash Editor tự nhận dạng"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="chỉ kiểm tra input đã có đủ giá trị through-wall hay chưa",
    )
    parser.add_argument(
        "--force", action="store_true", help="cho phép ghi đè file output đã tồn tại"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input.resolve()
    try:
        original = input_path.read_bytes()
        patched, changed = patched_bytes(original)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"LỖI: {error}", file=sys.stderr)
        return 2

    print(f"input_size={len(original)}")
    print(f"input_sha256={sha256(original)}")
    print(f"write_operations={len(WRITE_OFFSETS)}")
    print(f"target_bytes={len(TARGET_BYTES)}")

    if args.check:
        if changed:
            print(f"status=NOT_PATCHED changed_bytes_needed={len(changed)}")
            return 1
        print("status=PATCHED changed_bytes_needed=0")
        return 0

    output_path = (args.output or default_output_path(input_path)).resolve()
    if output_path == input_path:
        print("LỖI: không được ghi đè file Factory gốc", file=sys.stderr)
        return 2
    if not is_flash_editor_filename(output_path):
        print(
            "LỖI: tên output phải chứa _mtd_Factory_0x0-0x200000; "
            "nếu không Keenetic U-Boot Flash Editor sẽ không thể Restore file",
            file=sys.stderr,
        )
        return 2

    try:
        write_private_atomic(output_path, patched, force=args.force)
    except OSError as error:
        print(f"LỖI: {error}", file=sys.stderr)
        return 2

    written = output_path.read_bytes()
    if written != patched:
        print("LỖI: xác minh output sau khi ghi thất bại", file=sys.stderr)
        return 2

    print(f"changed_bytes={len(changed)}")
    print(f"output_size={len(written)}")
    print(f"output_sha256={sha256(written)}")
    print(f"output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
