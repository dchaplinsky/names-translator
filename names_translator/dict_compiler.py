"""Compile validated uk->ru name CSVs into per-pool DAWG dictionaries.

Input CSVs must have columns: uk, ru, count. Multiple files per pool are
merged; duplicate (uk, ru) pairs get their counts summed. Counts are
relative ranking weights, not necessarily corpus frequencies — e.g. the
bundled data-src/legacy_ua2ru.csv uses synthetic 2/1 weights that encode
primary/alternative order (so beware --min-count on it). The storage format
(record layout and rule encoding) is owned by names_translator.dicts — see
FORMAT_VERSION, RECORD_FORMAT and make_rule there.

Building requires the DAWG2 package (C extension, e.g. via
``pip install names_translator[fast]``); reading at runtime only needs the
pure-python dawg2-python.

Usage:
    python -m names_translator.dict_compiler --<pool> input.csv [...] \
        --out-dir names_translator/data

The canonical recipe for rebuilding the bundled data lives in
data-src/README.md in the source repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import defaultdict

from . import __version__
from ._text import normalize_key
from .dicts import FORMAT_VERSION, MAX_RANK, MAX_RULES, POOLS, RECORD_FORMAT, make_rule


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fp:
        for block in iter(lambda: fp.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_pairs(paths: list[str]) -> tuple[dict, int]:
    """Merge CSVs into {(normalized_uk, ru): total_count}."""
    counts: dict[tuple[str, str], int] = defaultdict(int)
    rows_read = 0

    for path in paths:
        with open(path, encoding="utf8") as fp:
            for row in csv.DictReader(fp):
                rows_read += 1
                uk, ru = row["uk"].strip(), row["ru"].strip()
                if not uk or not ru:
                    continue
                counts[(normalize_key(uk), ru)] += int(row["count"])

    return counts, rows_read


def compile_category(
    paths: list[str], out_dir: str, category: str, min_count: int, max_variants: int
) -> dict:
    import dawg  # the build-only DAWG2 dependency

    counts, rows_read = read_pairs(paths)

    by_key: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for (key, ru), count in counts.items():
        if count >= min_count:
            by_key[key].append((count, ru))

    rules: dict[tuple[int, str, bool], int] = {}
    records = []
    for key, variants in by_key.items():
        variants.sort(key=lambda cv: (-cv[0], cv[1]))
        for rank, (_, ru) in enumerate(variants[:max_variants]):
            rule_id = rules.setdefault(make_rule(key, ru), len(rules))
            if rule_id >= MAX_RULES:
                raise ValueError(
                    "%s: rule table exceeds the %d ids the record layout "
                    "allows" % (category, MAX_RULES)
                )
            records.append((key, (rank, rule_id)))

    dawg_path = os.path.join(out_dir, "%s.dawg" % category)
    rules_path = os.path.join(out_dir, "%s.rules.json" % category)

    dawg.RecordDAWG(RECORD_FORMAT, records).save(dawg_path)
    with open(rules_path, "w", encoding="utf8") as fp:
        # Insertion order equals rule id order by construction
        json.dump([list(rule) for rule in rules], fp, ensure_ascii=False)

    return {
        "sources": [
            {"file": os.path.basename(p), "sha256": sha256_file(p)} for p in paths
        ],
        "rows_read": rows_read,
        "pairs_kept": len(records),
        "unique_keys": len(by_key),
        "rules": len(rules),
        "verbatim_rules": sum(1 for _, _, titlecase in rules if not titlecase),
        "dawg_size": os.path.getsize(dawg_path),
        "dawg_sha256": sha256_file(dawg_path),
        "rules_size": os.path.getsize(rules_path),
        "rules_sha256": sha256_file(rules_path),
    }


def compile_dicts(
    pools: dict[str, list[str]],
    out_dir: str,
    min_count: int = 1,
    max_variants: int = 5,
) -> dict:
    """Compile all given pools and write the manifest; returns it."""
    os.makedirs(out_dir, exist_ok=True)

    manifest = {
        "format_version": FORMAT_VERSION,
        "names_translator_version": __version__,
        "options": {
            "min_count": min_count,
            "max_variants_per_key": max_variants,
        },
        "categories": {
            pool: compile_category(paths, out_dir, pool, min_count, max_variants)
            for pool, paths in pools.items()
            if paths
        },
    }

    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf8") as fp:
        json.dump(manifest, fp, ensure_ascii=False, indent=2)

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for pool in POOLS:
        parser.add_argument(
            "--%s" % pool, nargs="+", default=[], help="%s names CSVs" % pool
        )
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--min-count", type=int, default=1)
    parser.add_argument("--max-variants-per-key", type=int, default=5)
    args = parser.parse_args()

    if args.max_variants_per_key > MAX_RANK + 1:
        parser.error("--max-variants-per-key cannot exceed %d" % (MAX_RANK + 1))

    pools = {pool: getattr(args, pool) for pool in POOLS}
    if not any(pools.values()):
        parser.error("no input files given")

    manifest = compile_dicts(
        pools, args.out_dir, args.min_count, args.max_variants_per_key
    )

    for category, stats in manifest["categories"].items():
        print(
            "%s: %d rows -> %d keys, %d pairs, %d rules (%d verbatim), %.1f KB dawg + %.1f KB rules"
            % (
                category,
                stats["rows_read"],
                stats["unique_keys"],
                stats["pairs_kept"],
                stats["rules"],
                stats["verbatim_rules"],
                stats["dawg_size"] / 1024,
                stats["rules_size"] / 1024,
            )
        )


if __name__ == "__main__":
    main()
