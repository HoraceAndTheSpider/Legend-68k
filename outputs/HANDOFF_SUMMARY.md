# Consolidated hand-off summary

This hand-off was created because individual earlier file/directory links in the conversation were not reliably accessible. The goal is to preserve the investigation as one self-contained continuation point.

## What is included

- Every unique generated investigation artifact still materialised from the earlier turns, consolidated under `generated_resources/` by its logical output path. Duplicate backend copies with identical SHA-256 hashes were collapsed; no conflicting versions were found for the same logical path.
- The two earlier ZIP bundles exactly as generated.
- The generated initial archive inventory.
- The intermediate graphics extraction Python script from the thread.
- A new clean PAC-only Python decompressor containing the verified codec and no stale graphics assumptions.
- A freshly regenerated lossless `.raw` version of every one of the 93 supplied PAC files.
- Full PAC resource- and block-level manifests, including hashes and all 296 block records.
- A current regeneration of every A00-A10 base scene and every source-described overlay, with source dimensions, positions, exact animation byte sequences, composites, and 2x previews. This recreates the scene directories that had been described in the thread but were not all still available as individual downloadable files.
- Recreated D.TAP/m.tap historical page/tall diagnostics and DEGAS-candidate probe files that had been generated earlier but were not all still materialised.
- A native 320x200 copy of the previously retained 2x spell-book/background image, alongside the original 2x artifact.
- Exhaustive technical notes, current-status/supersession guidance, PAC-format documentation, complete file index and SHA-256 list.

## What is not silently claimed

The archive does not pretend that every PNG is a final decoded game asset. Historical probes are intentionally retained. The current/superseded distinction is recorded in `CURRENT_STATUS_AND_SUPERSESSIONS.md`.

The unresolved object-icon directory in SPELBITS, exact Axx `$80-$8F` animation control semantics, context-dependent three-plane palette remapping, and the first three nested WORLD resources remain research targets rather than being filled with guesses.

## Original input

The original `Legend_Mindscape.zip` is not duplicated in this generated-output archive. Its SHA-256 is recorded in `SOURCE_PROVENANCE.md` so the same input can be verified when work resumes.
