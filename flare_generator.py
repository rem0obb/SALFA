#!/usr/bin/env python3
"""Generate the JLR Gen21 activation code recovered from the firmware."""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path
from typing import Iterable


REGIONS = ("JP", "EU", "US", "PA", "CN", "KR", "TW", "ME", "RU", "ZA", "SA", "SE")
SALT_SIZE = 160
DEFAULT_UPDATE_SEED = bytes.fromhex(
    "2020022100010101000004ad01647584"
    "00000000000000000000000000000000"
    "0001000004ad01647584010000000000"
    "0000000000000000000000000000a600"
    "00014d00000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
)


def read_update_seed(path: str | Path | None = None) -> bytes:
    """Return the bundled seed or read 0xa0 bytes from another UPDATE.INF."""
    if path is None:
        return DEFAULT_UPDATE_SEED
    with Path(path).open("rb") as stream:
        seed = stream.read(SALT_SIZE)
    if len(seed) != SALT_SIZE:
        raise ValueError(f"UPDATE.INF must contain at least {SALT_SIZE} bytes")
    return seed


# Kept as an API alias for callers of the first recovered implementation.
read_media_seed = read_update_seed


def generate_code(vin: str, media_seed: bytes, region: str = "EU") -> str:
    """Return the eight-digit code checked by the firmware."""
    region = region.upper()
    if region not in REGIONS:
        raise ValueError(f"unsupported region {region!r}; expected one of {', '.join(REGIONS)}")
    if len(vin) != 17:
        raise ValueError("VIN must contain exactly 17 characters")
    try:
        vin_bytes = vin.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("VIN must contain ASCII characters only") from error
    if len(media_seed) != SALT_SIZE:
        raise ValueError(f"media seed must contain exactly {SALT_SIZE} bytes")

    # The receiver in MIUT_WPR always overwrites byte zero with ASCII 'S'.
    normalized_vin = b"S" + vin_bytes[1:]
    product = f"FiE_Gen21_NAVI_00_{region}".encode("ascii")
    digest = hashlib.sha1(product + normalized_vin + media_seed).digest()
    words = struct.unpack(">5I", digest)
    folded = words[0] ^ words[1] ^ words[2] ^ words[3] ^ words[4]
    return f"{folded:08X}"


def generate_many(vins: Iterable[str], media_seed: bytes, region: str = "EU") -> list[tuple[str, str]]:
    return [(vin, generate_code(vin, media_seed, region)) for vin in vins]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate JLR Gen21 codes using the first 160 bytes of UPDATE.INF."
    )
    parser.add_argument("vin", nargs="+", help="one or more 17-character VINs")
    parser.add_argument("--region", choices=REGIONS, default="EU", help="firmware region (default: EU)")
    parser.add_argument(
        "--update-inf",
        type=Path,
        help="use another update media's UPDATE.INF instead of the bundled CTF profile",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        seed = read_update_seed(args.update_inf)
        results = generate_many(args.vin, seed, args.region)
    except FileNotFoundError:
        print(
            f"error: UPDATE.INF not found at {args.update_inf}",
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for vin, code in results:
        print(f"{vin} -> {code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
