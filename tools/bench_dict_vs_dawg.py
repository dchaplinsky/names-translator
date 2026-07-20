#!/usr/bin/env python
"""Benchmark: naive dict-of-CSVs vs compiled DAWG dictionaries.

Each mode runs in a fresh subprocess so peak RSS is clean. The dict mode
loads the given uk,ru,count CSVs into a plain {key: [ru, ...]} dict; the
dawg modes load compiled dictionaries via names_translator.dicts.NameDicts
(dawg-fast uses the DAWG2 C reader instead of dawg2-python).

Usage:
    python tools/bench_dict_vs_dawg.py \
        --csv first.csv last.csv patronymics.csv \
        --dicts-dir dicts-dist/names_translator_dicts_uk/data
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import resource
import subprocess
import sys
import time
from typing import Callable

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

LOOKUPS = 100_000


def rss_mb() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is bytes on macOS, kilobytes on Linux
    return peak / (1 << 20) if sys.platform == "darwin" else peak / (1 << 10)


def sample_keys(csv_paths: list[str], limit: int = 20_000) -> list[str]:
    from names_translator import normalize_key

    keys = []
    for path in csv_paths:
        with open(path, encoding="utf8") as fp:
            for i, row in enumerate(csv.DictReader(fp)):
                if i % 7 == 0:
                    keys.append(normalize_key(row["uk"]))
                if len(keys) >= limit:
                    return keys
    return keys


def measure(csv_paths: list[str], load: Callable[[], Callable]) -> dict:
    base_rss = rss_mb()

    t0 = time.perf_counter()
    lookup = load()
    load_s = time.perf_counter() - t0

    # Pre-expanded so the harness adds no per-iteration index arithmetic
    keys = sample_keys(csv_paths)
    seq = (keys * (LOOKUPS // len(keys) + 1))[:LOOKUPS]
    t0 = time.perf_counter()
    for key in seq:
        lookup(key)
    lookup_s = time.perf_counter() - t0

    return {
        "load_ms": load_s * 1000,
        "rss_mb": rss_mb() - base_rss,
        "lookups_per_s": LOOKUPS / lookup_s,
    }


def load_dict(csv_paths: list[str]) -> Callable:
    from collections import defaultdict

    from names_translator import normalize_key

    data = defaultdict(list)
    for path in csv_paths:
        with open(path, encoding="utf8") as fp:
            for row in csv.DictReader(fp):
                data[normalize_key(row["uk"])].append(row["ru"])

    return data.get


def load_dawg(dicts_dir: str, fast: bool) -> Callable:
    if not fast:
        sys.modules["dawg"] = None  # force the pure-python reader
    from names_translator.dicts import NameDicts

    dicts = NameDicts(path=dicts_dir)
    dicts.lookup_key("")  # no category: warms every DAWG

    return lambda key: dicts.lookup_key(key, "last")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", nargs="+", required=True)
    parser.add_argument("--dicts-dir", required=True)
    parser.add_argument("--mode", choices=["dict", "dawg", "dawg-fast"])
    args = parser.parse_args()

    if args.mode:  # child process
        if args.mode == "dict":
            load = lambda: load_dict(args.csv)
        else:
            load = lambda: load_dawg(args.dicts_dir, args.mode == "dawg-fast")
        print(json.dumps(measure(args.csv, load)))
        return

    for mode in ("dict", "dawg", "dawg-fast"):
        proc = subprocess.run(
            [sys.executable, __file__, "--mode", mode, "--csv", *args.csv,
             "--dicts-dir", args.dicts_dir],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print("%s: FAILED\n%s" % (mode, proc.stderr.strip()))
            continue
        r = json.loads(proc.stdout)
        print(
            "%-10s load %8.1f ms   RSS %+7.1f MB   %10.0f lookups/s"
            % (mode, r["load_ms"], r["rss_mb"], r["lookups_per_s"])
        )


if __name__ == "__main__":
    main()
