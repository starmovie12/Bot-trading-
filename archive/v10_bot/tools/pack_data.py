#!/usr/bin/env python3
"""Data pack for the agent (MISSION V11 §10 item 3). Runs on the owner's machine; standard library only.

  python3 tools/pack_data.py [--data data/recorder] [--out .]      write datapack_<from>_<to>.zip
  python3 tools/pack_data.py --verify PACK [--into DIR]            check every checksum; extract into DIR

Only sealed day files (`YYYY-MM-DD.jsonl.gz`) and their `.sha256` sidecars go in, plus MANIFEST.sha256.
Nothing else can enter a pack, so a token file never does. A pack with any other name, a path outside the
pack, or a wrong checksum is refused.
"""

from __future__ import annotations

import hashlib
import re
import sys
import zipfile
from pathlib import Path

DAY = re.compile(r"^\d{4}-\d{2}-\d{2}\.jsonl\.gz(\.sha256)?$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack(data_dir: Path, out_dir: Path) -> Path:
    days = sorted(p for p in data_dir.glob("*.jsonl.gz") if DAY.match(p.name))
    if not days:
        raise SystemExit("no sealed day files to pack")
    manifest = []
    for gz in days:
        side = gz.with_name(gz.name + ".sha256")
        if not side.is_file() or side.read_text().split()[0] != sha(gz.read_bytes()):
            raise SystemExit(f"{gz.name}: sidecar checksum missing or wrong; not packed")
        manifest += [f"{sha(gz.read_bytes())}  {gz.name}", f"{sha(side.read_bytes())}  {side.name}"]
    first, last = days[0].name[:10], days[-1].name[:10]
    out = out_dir / f"datapack_{first}_{last}.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as z:
        for gz in days:
            z.write(gz, gz.name)
            z.write(gz.with_name(gz.name + ".sha256"), gz.name + ".sha256")
        z.writestr("MANIFEST.sha256", "\n".join(manifest) + "\n")
    return out


def verify(pack_path: Path, into: Path | None) -> int:
    with zipfile.ZipFile(pack_path) as z:
        names = z.namelist()
        bad = [n for n in names if n != "MANIFEST.sha256" and not DAY.match(n)]
        if bad or "MANIFEST.sha256" not in names:
            print(f"REFUSED: unexpected entries {bad[:3]} or no manifest")
            return 1
        listed: dict[str, str] = {}
        for line in z.read("MANIFEST.sha256").decode().splitlines():
            digest, name = line.split("  ", 1)
            listed[name] = digest
        problems = [n for n in names if n != "MANIFEST.sha256" and listed.get(n) != sha(z.read(n))]
        problems += [n for n in listed if n not in names]
        if problems:
            print(f"REFUSED: checksum mismatch or missing file: {problems[:3]}")
            return 1
        if into is not None:
            into.mkdir(parents=True, exist_ok=True)
            for n in names:
                if n != "MANIFEST.sha256":
                    (into / n).write_bytes(z.read(n))
    print(f"OK: {len(names) - 1} files, every checksum matches")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--verify"] and len(argv) >= 2:
        into = Path(argv[argv.index("--into") + 1]) if "--into" in argv else None
        return verify(Path(argv[1]), into)
    data = Path(argv[argv.index("--data") + 1]) if "--data" in argv else Path("data/recorder")
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else Path(".")
    print(pack(data, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
