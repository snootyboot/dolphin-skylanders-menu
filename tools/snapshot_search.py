#!/usr/bin/env python3
"""Find memory addresses from roguelike dev-tools capture sessions.

Each capture session folder holds manifest.json and one .snap.zst file per captured step.
Rules describe how a value relates between steps; every address that obeys all rules is a
candidate.

Rules (labels come from session.txt; use "#3" to refer to capture index 3 instead):
  a>b        value went down from a to b
  a<b        value went up from a to b
  a=b        value is the same in a and b
  a!=b       value changed between a and b
  a==123     value at a equals 123 (int or float)
  a>=0  a<=1000  a!=0   compare one capture with a constant
  a<=b  a>=b             value didn't go up / didn't go down between captures
  a~b                    values are within --tol of each other (e.g. positions)

Example (gold goes up twice, stays put while standing still):
  snapshot_search.py CAPTURE_DIR --type u32 --rule "start<gold_1" --rule "gold_1<gold_2" \
      --rule "gold_2=nothing"
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import zstandard
except ImportError:  # pragma: no cover
    sys.exit("Needs the zstandard package: pip install zstandard")

MAGIC = b"SKRLSNAP"
HEADER_SIZE = 48
MEM1_BASE = 0x80000000
MEM2_BASE = 0x90000000

TYPES = {
    "u8": (">u1", 1),
    "u16": (">u2", 2),
    "u32": (">u4", 4),
    "s8": (">i1", 1),
    "s16": (">i2", 2),
    "s32": (">i4", 4),
    "f32": (">f4", 4),
    # Little-endian: raw Skylander figure data (gold, XP) is little-endian even on the Wii.
    "u16le": ("<u2", 2),
    "u32le": ("<u4", 4),
}


@dataclass
class Snapshot:
    index: int
    label: str
    frame: int
    mem1: np.ndarray  # uint8
    mem2: np.ndarray  # uint8


def read_snapshot(path: Path) -> tuple[int, np.ndarray, np.ndarray]:
    raw = path.read_bytes()
    data = zstandard.ZstdDecompressor().decompressobj().decompress(raw)
    if len(data) < HEADER_SIZE or data[:8] != MAGIC:
        raise ValueError(f"{path.name}: not a dev-tools snapshot")
    version, header_size, mem1_size, mem2_size, frame = struct.unpack_from("<IIIIQ", data, 8)
    if version != 1 or header_size != HEADER_SIZE:
        raise ValueError(f"{path.name}: unsupported snapshot version {version}")
    expected = header_size + mem1_size + mem2_size
    if len(data) != expected:
        raise ValueError(f"{path.name}: size {len(data)} != expected {expected} (truncated?)")
    buf = np.frombuffer(data, dtype=np.uint8)
    mem1 = buf[header_size : header_size + mem1_size]
    mem2 = buf[header_size + mem1_size : expected]
    return frame, mem1, mem2


def load_session(folder: Path) -> list[Snapshot]:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    snaps = []
    for entry in manifest["entries"]:
        if entry["status"] != "saved":
            continue
        frame, mem1, mem2 = read_snapshot(folder / entry["file"])
        snaps.append(Snapshot(entry["index"], entry["label"], frame, mem1, mem2))
    if not snaps:
        sys.exit("No saved captures in this session.")
    return snaps


RULE_RE = re.compile(r"^\s*([^<>=!~\s]+)\s*(==|!=|>=|<=|>|<|=|~)\s*(.+?)\s*$")


@dataclass
class Rule:
    left: str
    op: str
    right: str
    constant: float | None


def parse_rule(text: str) -> Rule:
    m = RULE_RE.match(text)
    if not m:
        raise ValueError(f"Bad rule: {text!r}")
    left, op, right = m.groups()
    constant = None
    try:
        constant = float(int(right, 0)) if re.fullmatch(r"-?(0x[0-9a-fA-F]+|\d+)", right) else float(right)
    except ValueError:
        constant = None
    if constant is None and op == "==":
        raise ValueError(f"Rule {text!r}: '==' needs a number on the right (use '=' between captures)")
    if constant is not None and op in ("=", ">", "<", "~"):
        raise ValueError(f"Rule {text!r}: use '==', '!=', '>=', '<=' with a number")
    return Rule(left, op, right, constant)


def find_snapshot(snaps: list[Snapshot], ref: str) -> Snapshot:
    if ref.startswith("#"):
        idx = int(ref[1:])
        for s in snaps:
            if s.index == idx:
                return s
        raise KeyError(f"No saved capture #{idx}")
    matches = [s for s in snaps if s.label == ref]
    if not matches:
        raise KeyError(f"No saved capture labelled {ref!r} (have: {', '.join(s.label for s in snaps)})")
    if len(matches) > 1:
        raise KeyError(f"Label {ref!r} is used by captures {[m.index for m in matches]}; use #index")
    return matches[0]


def view(mem: np.ndarray, dtype: str, size: int) -> np.ndarray:
    usable = (len(mem) // size) * size
    return mem[:usable].view(dtype)


def search(snaps: list[Snapshot], rules: list[Rule], type_name: str, region: str, tol: float = 1.0) -> np.ndarray:
    dtype, size = TYPES[type_name]
    mask = None
    cache: dict[int, np.ndarray] = {}

    def values(s: Snapshot) -> np.ndarray:
        if s.index not in cache:
            mem = s.mem1 if region == "mem1" else s.mem2
            cache[s.index] = view(mem, dtype, size)
        return cache[s.index]

    for rule in rules:
        a = values(find_snapshot(snaps, rule.left))
        if rule.constant is not None:
            c = rule.constant
            with np.errstate(invalid="ignore"):
                cond = {"==": a == c, "!=": a != c, ">=": a >= c, "<=": a <= c}[rule.op]
        else:
            b = values(find_snapshot(snaps, rule.right))
            with np.errstate(invalid="ignore"):
                if rule.op == "~":
                    cond = np.abs(a.astype(np.float64) - b.astype(np.float64)) <= tol
                else:
                    cond = {"<": a < b, ">": a > b, "=": a == b, "!=": a != b, "<=": a <= b, ">=": a >= b}[rule.op]
        if type_name == "f32":
            cond &= np.isfinite(a)
        mask = cond if mask is None else (mask & cond)
    if mask is None:
        return np.array([], dtype=np.int64)
    return np.nonzero(mask)[0] * size


def format_value(v) -> str:
    if isinstance(v, (np.floating, float)):
        return f"{float(v):.6g}"
    return str(int(v))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("session", type=Path, help="capture session folder (has manifest.json)")
    p.add_argument("--type", default="u32", choices=sorted(TYPES))
    p.add_argument("--rule", action="append", default=[], help="see above; repeatable")
    p.add_argument("--region", choices=["mem1", "mem2", "both"], default="both")
    p.add_argument("--limit", type=int, default=40, help="candidates to print")
    p.add_argument("--tol", type=float, default=1.0, help="tolerance for the a~b rule")
    p.add_argument("--watch-out", type=Path, help="write the top candidates as watch.txt lines")
    p.add_argument("--list", action="store_true", help="list the captures and exit")
    args = p.parse_args(argv)

    snaps = load_session(args.session)
    if args.list:
        for s in snaps:
            print(f"#{s.index:3}  {s.label:24}  frame {s.frame}")
        return 0
    if not args.rule:
        p.error("give at least one --rule")
    rules = [parse_rule(r) for r in args.rule]

    _, size = TYPES[args.type]
    results = []
    for region in (["mem1", "mem2"] if args.region == "both" else [args.region]):
        base = MEM1_BASE if region == "mem1" else MEM2_BASE
        offsets = search(snaps, rules, args.type, region, args.tol)
        for off in offsets:
            results.append((region, base + int(off), int(off)))

    print(f"{len(results)} candidate(s) for {args.type} with {len(rules)} rule(s)")
    shown = results[: args.limit]
    header = "address     " + "  ".join(f"{s.label[:12]:>12}" for s in snaps)
    if shown:
        print(header)
    dtype, _ = TYPES[args.type]
    for region, addr, off in shown:
        vals = []
        for s in snaps:
            mem = s.mem1 if region == "mem1" else s.mem2
            vals.append(format_value(mem[off : off + size].view(dtype)[0]))
        print(f"0x{addr:08X}  " + "  ".join(f"{v:>12}" for v in vals))

    if args.watch_out and shown:
        type_name = "f32" if args.type == "f32" else args.type
        lines = [f"cand_{i + 1}_{addr:08X} | {type_name} | 0x{addr:08X}" for i, (_, addr, _) in enumerate(shown[:20])]
        args.watch_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {len(lines)} watch lines to {args.watch_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
