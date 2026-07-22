# Dictionary source data

## legacy_ua2ru.csv

Converted from the historical `names_translator/data/ua2ru.csv`
(`term,translation,alt_translation`; removed in 2.1.0 — see git history) into
the standard compiler format `uk,ru,count`.

**The counts are synthetic ranking weights, not corpus frequencies**: 2 marks
the primary translation, 1 the alternative, which preserves their original
order after the compiler ranks variants by count. Do not filter this file
with `--min-count` above 1, and do not merge it with real-frequency sources.

The three category pools (`first`, `patronymic`, `last`) are compiled from
private validated dumps that are not in this repository; their file names and
sha256 checksums are recorded in `names_translator/data/manifest.json`.

## Rebuilding the bundled data

```bash
python -m names_translator.dict_compiler \
    --first first_names_validated.csv \
    --last last_names_validated.csv last_names_rescued.csv \
    --patronymic patronymics_validated.csv \
    --legacy data-src/legacy_ua2ru.csv \
    --out-dir names_translator/data
```

Requires the `DAWG2` builder (`pip install names_translator[fast]`).
