# Legend / Four Crystals of Trazere graphics investigation outputs

This directory is a consolidated hand-off of the resources produced during the ChatGPT investigation of the supplied Amiga game files. It is intended to be usable as a continuing research point and as the contents of a repository `outputs/` directory.

The original supplied game archive itself is deliberately **not duplicated** inside this output set. Its SHA-256 is recorded in `SOURCE_PROVENANCE.md`. Everything else here is generated, extracted, decoded, probed, documented, or reconstructed from the investigation.

## Important distinction: current results vs historical probes

The investigation deliberately retained experiments as evidence. Some early images were produced before the correct PAC decompressor, palette source, picture dimensions, or internal table layouts were known. They are useful diagnostics, but they are not all valid final conversions.

Use these folders as follows:

- `reconstructed_current/` — current source-backed reconstructions made for this consolidated hand-off. These should be preferred where they overlap older probes.
- `raw_pac/` — losslessly decompressed output of every supplied `.PAC` resource, using the now-verified PAC algorithm. There are 93 raw resources.
- `generated_resources/` — every unique investigation artifact still materialised from earlier turns, preserving its logical path. This contains both strong results and historical/incorrect probes.
- `reconstructed_historical/` — historical probe outputs recreated because earlier individual downloads were no longer materialised. They are explicitly diagnostic, not promoted as authoritative graphics layouts.
- `tools/` — the intermediate all-in-one graphics extractor from the thread, plus a clean verified PAC-only decompressor with no graphics assumptions.
- `inventory/` — archive inventory produced during the initial investigation.
- `historical_bundles/` — earlier ZIP bundles produced during the conversation. They are included because the request is to preserve every generated resource, even though their contents overlap other files here.

Read `CURRENT_STATUS_AND_SUPERSESSIONS.md` before using old contact sheets programmatically.

## Core documents

- `INVESTIGATION_NOTES_COMPLETE.md` — consolidated technical record of the full investigation and all significant findings, including unresolved points.
- `CURRENT_STATUS_AND_SUPERSESSIONS.md` — which interpretations are current, which are provisional, and which are known to be wrong.
- `PAC_FORMAT.md` — exact PAC structure and decompression algorithm.
- `PAC_RESOURCE_MANIFEST.tsv` — one row per supplied PAC resource with packed/unpacked sizes and SHA-256 hashes.
- `PAC_BLOCK_MANIFEST.tsv` — one row per PAC compression block. The supplied set contains 296 blocks in 93 PAC files.
- `RESOURCE_INDEX.tsv` — complete index of the consolidated hand-off, with paths, sizes and SHA-256 hashes.
- `FILES_SHA256.txt` — checksum list for every file in this output set.
- `SOURCE_PROVENANCE.md` — checksum and treatment of the original input archive.

## Verified PAC command-line tool

`tools/legend_pac_decompress.py` is the safest starting point for future work because it contains only the PAC parser/decompressor and does not encode any obsolete graphics-layout assumptions.

Examples:

```bash
python tools/legend_pac_decompress.py verify /path/to/extracted/game
python tools/legend_pac_decompress.py info /path/to/PARTY.PAC
python tools/legend_pac_decompress.py unpack /path/to/extracted/game -o raw
```

The older `tools/legend_graphics_extract_intermediate.py` is preserved exactly as a thread artifact. Its PAC decompression core is valid, but some of its graphics recipes are superseded: notably its `UINV.PAC = 128x44` treatment and its default use of `D.TAP` as a general gameplay palette.

## Recommended GitHub placement

Using this directory as `outputs/` is a sensible organisation for continuing technical work. I would keep code that becomes maintained tooling in a repository-level `tools/` directory eventually, while leaving snapshots, contact sheets, raw decompressions and audit manifests under `outputs/`.

If the repository will be public, note that the PNGs and raw decompressed resources contain derived game artwork/data. Whether those should be published is a separate copyright/licensing decision from publishing the reverse-engineering code and documentation.
