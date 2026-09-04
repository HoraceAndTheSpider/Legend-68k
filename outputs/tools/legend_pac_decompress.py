#!/usr/bin/env python3
"""Verified Legend / Four Crystals of Trazere PAC decompressor.

This file contains only the PAC container/parser/decompression logic established
in the investigation.  It deliberately contains no graphics-layout assumptions.

PAC block, big-endian:
    word 0: bit 15 = another block follows; low 15 bits = rule_count - 1
    word 1: payload_size - 1
    key[rule_count]
    table2[rule_count]
    table3[rule_count]
    payload[payload_size]

To expand a block, process substitution rules from the last rule to the first
and replace each key byte with the pair: table3[i], table2[i].  Concatenate the
expanded blocks in file order.

The rule order and table3/table2 output order were checked against the supplied
68000 loader and across every supplied PAC resource.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PacBlock:
    offset: int
    continuation: bool
    rule_count: int
    payload_size: int
    keys: bytes
    table2: bytes
    table3: bytes
    payload: bytes


def parse_pac(data: bytes) -> list[PacBlock]:
    blocks: list[PacBlock] = []
    pos = 0
    while pos < len(data):
        if pos + 4 > len(data):
            raise ValueError(f"truncated PAC header at 0x{pos:X}")
        header = int.from_bytes(data[pos:pos + 2], "big")
        continuation = bool(header & 0x8000)
        rule_count = (header & 0x7FFF) + 1
        payload_size = int.from_bytes(data[pos + 2:pos + 4], "big") + 1

        key_start = pos + 4
        t2_start = key_start + rule_count
        t3_start = t2_start + rule_count
        payload_start = t3_start + rule_count
        end = payload_start + payload_size
        if end > len(data):
            raise ValueError(
                f"truncated PAC block at 0x{pos:X}: expected end 0x{end:X}, "
                f"file ends at 0x{len(data):X}"
            )
        blocks.append(PacBlock(
            offset=pos,
            continuation=continuation,
            rule_count=rule_count,
            payload_size=payload_size,
            keys=data[key_start:t2_start],
            table2=data[t2_start:t3_start],
            table3=data[t3_start:payload_start],
            payload=data[payload_start:end],
        ))
        pos = end
        if not continuation:
            break

    if not blocks:
        raise ValueError("empty PAC file")
    if pos != len(data):
        raise ValueError(f"PAC has {len(data) - pos} trailing byte(s) after final block")
    return blocks


def unpack_block(block: PacBlock) -> bytes:
    out = block.payload
    for i in range(block.rule_count - 1, -1, -1):
        out = out.replace(bytes((block.keys[i],)), bytes((block.table3[i], block.table2[i])))
    return out


def unpack_pac(data: bytes) -> tuple[bytes, list[PacBlock], list[bytes]]:
    blocks = parse_pac(data)
    parts = [unpack_block(block) for block in blocks]
    return b"".join(parts), blocks, parts


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


def cmd_info(path: Path) -> None:
    raw = path.read_bytes()
    unpacked, blocks, parts = unpack_pac(raw)
    print(f"{path}: packed={len(raw)} unpacked={len(unpacked)} blocks={len(blocks)}")
    for n, (block, part) in enumerate(zip(blocks, parts)):
        print(
            f"  {n:02d} off=0x{block.offset:06X} rules={block.rule_count:3d} "
            f"payload={block.payload_size:5d} unpacked={len(part):6d} "
            f"continue={'yes' if block.continuation else 'no'}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description="Verified Legend PAC decompressor")
    sp = ap.add_subparsers(dest="command", required=True)
    p = sp.add_parser("info")
    p.add_argument("input")
    p = sp.add_parser("unpack")
    p.add_argument("input")
    p.add_argument("-o", "--output", required=True)
    p = sp.add_parser("verify")
    p.add_argument("input")
    args = ap.parse_args()

    source = Path(args.input)
    if args.command == "info":
        cmd_info(source)
        return 0

    paths = list(iter_pacs(source)) if source.is_dir() else [source]
    if args.command == "verify":
        for path in paths:
            unpack_pac(path.read_bytes())
        print(f"Verified {len(paths)} PAC file(s).")
        return 0

    output = Path(args.output)
    for path in paths:
        unpacked, blocks, _parts = unpack_pac(path.read_bytes())
        rel = path.relative_to(source) if source.is_dir() else Path(path.name)
        dest = output / rel.with_suffix(rel.suffix + ".raw")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(unpacked)
        print(f"{rel}: {path.stat().st_size} -> {len(unpacked)} bytes ({len(blocks)} block(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
