#!/usr/bin/env python3
"""Extract and convert graphics resources from Mindscape/TAG Legend (Amiga).

The .PAC depacker is derived from the supplied game data and confirmed against
Legend's 68000 loader in C/leggo.  PAC blocks use a compact byte-pair
substitution dictionary.

Block layout (all sizes stored as terminal DBRA-style counts):

    +0  byte   continuation/rule-count high bit (bit 7 = another block)
    +1  byte   rule_count - 1
    +2  word   payload_size - 1 (big endian)
    +4         key[rule_count]
               table2[rule_count]
               table3[rule_count]
               payload[payload_size]

The first two bytes are read by the 68000 as one word.  The loader masks bit 15
with ANDI.W #$7FFF, leaving rule_count-1 in D4, then uses indexed LEAs with a
+1 displacement to step across the three arrays.  The payload count is consumed
with DBF/DBRA, hence its stored value is also one less than the byte count.

Rules were created as staged byte-pair substitutions.  The 68000 expander emits
table3[i] first and table2[i] second for key[i].  To unpack equivalently, apply
the rules in reverse order to the payload as key -> table3,table2.  This produces exact fixed-size outputs
for resource families such as PARTY (32000 bytes), SPIT/M00-M21 (15360 bytes),
PRUMS/Rxx (2048 bytes), and SPIT/M80-M87 (1024 bytes).

Known graphical layouts currently supported:
  PARTY.PAC       320x200, 4 Amiga bitplanes stored plane-major
  UINV.PAC        128x44,  4 Amiga bitplanes stored plane-major
  SPIT/M00-M21    96x320,  4 Amiga bitplanes stored plane-major
  TILES2.PAC      355 tiles, 16x8, ST-style 4-plane words interleaved per row
  TILESX.PAC      224 tiles, 16x8, ST-style 4-plane words interleaved per row

Unknown/structured PACs are always written losslessly as .raw after depacking;
the tool does not invent dimensions for them.
"""
from __future__ import annotations

import argparse
import csv
import math
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


@dataclass(frozen=True)
class PacBlock:
    offset: int
    continuation: bool
    rule_count: int
    payload_size: int
    keys: bytes
    left: bytes
    right: bytes
    payload: bytes
    unpacked_size: int = 0


def parse_pac(data: bytes) -> list[PacBlock]:
    """Parse a complete Legend PAC file into blocks without unpacking it."""
    blocks: list[PacBlock] = []
    pos = 0
    while pos < len(data):
        if pos + 4 > len(data):
            raise ValueError(f"truncated PAC header at 0x{pos:X}")

        flag_count = int.from_bytes(data[pos:pos + 2], "big")
        continuation = bool(flag_count & 0x8000)
        stored_rule_count = flag_count & 0x7FFF
        # In every supplied file this fits in the low byte; writing it this way
        # mirrors the 68000 code and makes the continuation bit explicit.
        rule_count = stored_rule_count + 1
        payload_size = int.from_bytes(data[pos + 2:pos + 4], "big") + 1

        table_start = pos + 4
        left_start = table_start + rule_count
        right_start = left_start + rule_count
        payload_start = right_start + rule_count
        end = payload_start + payload_size
        if end > len(data):
            raise ValueError(
                f"truncated PAC block at 0x{pos:X}: expected end 0x{end:X}, "
                f"file ends at 0x{len(data):X}"
            )

        keys = data[table_start:left_start]
        left = data[left_start:right_start]
        right = data[right_start:payload_start]
        payload = data[payload_start:end]
        blocks.append(
            PacBlock(
                offset=pos,
                continuation=continuation,
                rule_count=rule_count,
                payload_size=payload_size,
                keys=keys,
                left=left,
                right=right,
                payload=payload,
            )
        )
        pos = end
        if not continuation:
            break

    if pos != len(data):
        raise ValueError(f"PAC has {len(data)-pos} trailing byte(s) after final block")
    if not blocks:
        raise ValueError("empty PAC file")
    return blocks


def unpack_block(block: PacBlock) -> bytes:
    """Expand one PAC block using its staged byte-pair dictionary."""
    buf = block.payload
    # Later rules can contain earlier rule symbols, so undo creation order.
    for i in range(block.rule_count - 1, -1, -1):
        key = bytes((block.keys[i],))
        # The 68000 routine expands A1 (third table) before A2 (second table).
        pair = bytes((block.right[i], block.left[i]))
        buf = buf.replace(key, pair)
    return buf


def unpack_pac_bytes(data: bytes) -> tuple[bytes, list[PacBlock], list[bytes]]:
    blocks = parse_pac(data)
    parts = [unpack_block(block) for block in blocks]
    return b"".join(parts), blocks, parts


def unpack_pac_file(path: Path) -> tuple[bytes, list[PacBlock], list[bytes]]:
    return unpack_pac_bytes(path.read_bytes())


def read_amiga_palette(path: Path) -> tuple[int, ...]:
    """Read the first 16 Amiga 12-bit RGB words from a resource such as D.TAP."""
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError(f"palette source {path} is shorter than 32 bytes")
    return struct.unpack_from(">16H", data, 0)


def palette_rgb8(words: Sequence[int]) -> list[int]:
    pal: list[int] = []
    for word in words[:16]:
        pal.extend((((word >> 8) & 0xF) * 17, ((word >> 4) & 0xF) * 17, (word & 0xF) * 17))
    return pal + [0] * (768 - len(pal))


def _need_pillow() -> None:
    if Image is None:
        raise RuntimeError("PNG export requires Pillow: pip install pillow")


def decode_amiga_plane_major(raw: bytes, width: int, height: int, palette: Sequence[int]):
    """Decode four contiguous Amiga bitplanes into a paletted Pillow image."""
    _need_pillow()
    if width % 8:
        raise ValueError("plane-major width must be a multiple of 8")
    row_bytes = width // 8
    plane_size = row_bytes * height
    expected = plane_size * 4
    if len(raw) != expected:
        raise ValueError(f"{width}x{height}x4 requires {expected} bytes, got {len(raw)}")

    image = Image.new("P", (width, height))
    image.putpalette(palette_rgb8(palette))
    pixels = image.load()
    for y in range(height):
        row = y * row_bytes
        for x in range(width):
            byte_index = row + (x >> 3)
            bit = 7 - (x & 7)
            colour = 0
            for plane in range(4):
                colour |= ((raw[plane * plane_size + byte_index] >> bit) & 1) << plane
            pixels[x, y] = colour
    return image


def decode_tile_16x8(tile: bytes, palette: Sequence[int]):
    """Decode one 64-byte 16x8 tile: four big-endian plane words per row."""
    _need_pillow()
    if len(tile) != 64:
        raise ValueError("16x8 four-plane tile must be exactly 64 bytes")
    image = Image.new("P", (16, 8))
    image.putpalette(palette_rgb8(palette))
    pixels = image.load()
    off = 0
    for y in range(8):
        planes = struct.unpack_from(">4H", tile, off)
        off += 8
        for x in range(16):
            mask = 1 << (15 - x)
            colour = 0
            for plane, word in enumerate(planes):
                colour |= int(bool(word & mask)) << plane
            pixels[x, y] = colour
    return image


def render_tile_atlas(raw: bytes, palette: Sequence[int], columns: int = 16):
    _need_pillow()
    if len(raw) % 64:
        raise ValueError(f"tile resource is not a multiple of 64 bytes: {len(raw)}")
    count = len(raw) // 64
    rows = math.ceil(count / columns)
    atlas = Image.new("P", (columns * 16, rows * 8))
    atlas.putpalette(palette_rgb8(palette))
    for index in range(count):
        tile = decode_tile_16x8(raw[index * 64:(index + 1) * 64], palette)
        atlas.paste(tile, ((index % columns) * 16, (index // columns) * 8))
    return atlas, count


def save_png(image, path: Path, scale: int = 1) -> None:
    _need_pillow()
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    if scale > 1:
        image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST).save(
            path.with_name(f"{path.stem}_{scale}x{path.suffix}")
        )


def known_png_layout(relative: Path):
    """Return a known rendering recipe, or None for structured/unknown data."""
    name = relative.name.upper()
    parent = relative.parent.name.upper()
    if name == "PARTY.PAC":
        return ("plane", 320, 200)
    if name == "UINV.PAC":
        return ("plane", 128, 44)
    if parent == "SPIT" and name.startswith("M") and name.endswith(".PAC"):
        try:
            number = int(name[1:3], 16)
        except ValueError:
            return None
        if 0x00 <= number <= 0x21:
            return ("plane", 96, 320)
    if name in {"TILES2.PAC", "TILESX.PAC"}:
        return ("tiles", 16, 8)
    return None


def iter_pacs(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if (
            path.is_file()
            and path.suffix.lower() == ".pac"
            and not path.name.endswith(".uaem")
            and not path.name.startswith("._")
            and "__MACOSX" not in path.parts
        ):
            yield path


def extract_tree(root: Path, output: Path, palette_path: Path | None, scale: int, tile_columns: int) -> list[dict[str, object]]:
    palette = read_amiga_palette(palette_path) if palette_path else None
    rows: list[dict[str, object]] = []
    for pac in iter_pacs(root):
        rel = pac.relative_to(root)
        raw, blocks, parts = unpack_pac_file(pac)
        raw_path = output / "raw" / rel.with_suffix(rel.suffix + ".raw")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(raw)

        recipe = known_png_layout(rel)
        png_status = "raw-only"
        png_path = ""
        if recipe and palette is not None:
            kind, width, height = recipe
            if kind == "plane":
                image = decode_amiga_plane_major(raw, width, height, palette)
                path = output / "png" / rel.with_suffix(".png")
                save_png(image, path, scale)
                png_path = str(path.relative_to(output))
                png_status = f"{width}x{height} Amiga plane-major"
            elif kind == "tiles":
                image, count = render_tile_atlas(raw, palette, tile_columns)
                path = output / "png" / rel.with_name(rel.stem + "_atlas.png")
                save_png(image, path, scale)
                png_path = str(path.relative_to(output))
                png_status = f"{count} x 16x8 interleaved-planar tiles"

        rows.append({
            "file": str(rel),
            "packed_size": pac.stat().st_size,
            "blocks": len(blocks),
            "unpacked_size": len(raw),
            "block_unpacked_sizes": ",".join(str(len(part)) for part in parts),
            "png_status": png_status,
            "png": png_path,
        })
    return rows


def write_manifest(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["file", "packed_size", "blocks", "unpacked_size", "block_unpacked_sizes", "png_status", "png"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def cmd_unpack(args) -> int:
    source = Path(args.input)
    output = Path(args.output)
    paths = list(iter_pacs(source)) if source.is_dir() else [source]
    for pac in paths:
        raw, blocks, parts = unpack_pac_file(pac)
        rel = pac.relative_to(source) if source.is_dir() else Path(pac.name)
        out = output / rel.with_suffix(rel.suffix + ".raw")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
        print(f"{rel}: {pac.stat().st_size} -> {len(raw)} bytes ({len(blocks)} block(s))")
    return 0


def cmd_extract(args) -> int:
    root = Path(args.input)
    output = Path(args.output)
    palette = Path(args.palette) if args.palette else root / "C" / "D.TAP"
    if not palette.exists():
        raise FileNotFoundError(f"palette source not found: {palette}")
    rows = extract_tree(root, output, palette, args.scale, args.tile_columns)
    write_manifest(rows, output / "manifest.tsv")
    converted = sum(1 for row in rows if row["png_status"] != "raw-only")
    print(f"Processed {len(rows)} PAC files; rendered {converted} known graphical resources/families.")
    print(f"Manifest: {output / 'manifest.tsv'}")
    return 0


def cmd_info(args) -> int:
    pac = Path(args.input)
    raw, blocks, parts = unpack_pac_file(pac)
    print(f"{pac}: packed={pac.stat().st_size} unpacked={len(raw)} blocks={len(blocks)}")
    for i, (block, part) in enumerate(zip(blocks, parts)):
        print(
            f"  {i:02d} off=0x{block.offset:06X} rules={block.rule_count:3d} "
            f"payload={block.payload_size:5d} unpacked={len(part):6d} "
            f"continue={'yes' if block.continuation else 'no'}"
        )
    return 0


def cmd_verify(args) -> int:
    root = Path(args.input)
    paths = list(iter_pacs(root))
    failures = []
    for pac in paths:
        try:
            raw, blocks, parts = unpack_pac_file(pac)
            # Re-parse exact end/continuation semantics are already checked by parser.
            if any(not part for part in parts):
                raise ValueError("empty unpacked block")
        except Exception as exc:
            failures.append((pac, exc))
    if failures:
        for pac, exc in failures:
            print(f"FAIL {pac}: {exc}", file=sys.stderr)
        return 1
    print(f"Verified {len(paths)} PAC files: all blocks parse and depack to exact file boundaries.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Legend PAC depacker and graphics converter")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("unpack", help="depack PAC file(s) to raw bytes")
    p.add_argument("input", help="PAC file or extracted game root")
    p.add_argument("-o", "--output", required=True)
    p.set_defaults(func=cmd_unpack)

    p = sub.add_parser("extract", help="depack all PACs and render known graphics as PNG")
    p.add_argument("input", help="extracted game root containing C/, PACS/, SPIT/, PRUMS/")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--palette", help="palette file (default: C/D.TAP)")
    p.add_argument("--scale", type=int, default=2, help="also write nearest-neighbour Nx PNG (default 2)")
    p.add_argument("--tile-columns", type=int, default=16, help="columns in TILES2/TILESX atlases")
    p.set_defaults(func=cmd_extract)

    p = sub.add_parser("info", help="show PAC block structure")
    p.add_argument("input")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("verify", help="parse/depack every PAC in a tree")
    p.add_argument("input")
    p.set_defaults(func=cmd_verify)
    return parser


def main() -> int:
    return build_parser().parse_args().func(build_parser().parse_args())


if __name__ == "__main__":
    # Avoid parsing twice (kept explicit to make the module import-safe).
    parser = build_parser()
    ns = parser.parse_args()
    raise SystemExit(ns.func(ns))
