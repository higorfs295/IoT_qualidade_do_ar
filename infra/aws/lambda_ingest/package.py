#!/usr/bin/env python3
"""Gera um ZIP determinístico e autocontido para a Lambda de ingestão."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CONTRACT = ROOT / "poc" / "qar_poc"
DEFAULT_OUTPUT = HERE.parent / "dist" / "qar-lambda-ingest.zip"


def _write(zf: ZipFile, source: Path, archive_name: str) -> None:
    info = ZipInfo(archive_name, date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    zf.writestr(info, source.read_bytes())


def build(output: Path) -> tuple[Path, str]:
    if not (HERE / "handler.py").is_file() or not CONTRACT.is_dir():
        raise FileNotFoundError("handler ou pacote qar_poc não encontrado")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w") as zf:
        _write(zf, HERE / "handler.py", "handler.py")
        for source in sorted(CONTRACT.glob("*.py")):
            _write(zf, source, f"qar_poc/{source.name}")
    with ZipFile(output) as zf:
        names = set(zf.namelist())
        required = {"handler.py", "qar_poc/__init__.py", "qar_poc/contrato.py"}
        if not required.issubset(names) or any("__pycache__" in name for name in names):
            raise RuntimeError("ZIP gerado não passou na verificação estrutural")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return output, digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output, digest = build(args.output.resolve())
    print(f"arquivo={output}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
