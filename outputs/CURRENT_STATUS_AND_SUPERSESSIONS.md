# Current status and superseded interpretations

This file is the quick guide to which investigation outputs should be trusted as current format interpretations.

## Current / high confidence

### PAC decompression

Solved and verified across all supplied PACs. See `PAC_FORMAT.md`.

### `C/4XEUR` and `C/BEUR`

Confirmed DEGAS Elite compressed Atari ST low-resolution pictures. Both decode as 320x200, 16-colour images. The PNGs are retained under `generated_resources/legend_graphics/`.

### Hard-coded gameplay palette

The investigation located 16-colour palette data in `C/leggo`. The principal gameplay palette used for the corrected Axx scene work was tracked during the investigation with the probe label/offset `0x1D6D6`. Two additional palette probes were labelled `0x3E5A6` and `0x3E5C6` in earlier outputs. The main palette produced the convincing normal gameplay appearance for location scenes.

`reconstructed_current/scenes/gameplay_palette_main_0x1D6D6.tsv` records the 16 words used in the current scene reconstruction.

### A00-A10 location/encounter resources

Substantially decoded and regenerated in `reconstructed_current/scenes/`.

Each Axx resource has a table-driven structure. The current reconstruction reads the resource's own graphics-offset table, overlay descriptor table and 32 animation-sequence pointers.

The base picture is 160x96, four-plane, interleaved Atari-ST-style words, consuming exactly `$1E00` bytes.

Overlay descriptor records are four big-endian words:

```text
word 0  width in 16-pixel words - 1
word 1  height - 1
word 2  destination X
word 3  destination Y
```

The overlay byte sizes calculated from those fields match successive graphics offsets across the families, with explicitly noted trailing/extra data cases.

The 32 animation slots are preserved as exact byte sequences. Control bytes in the `$80-$8F` range have not yet been assigned final timing/behaviour semantics, so no timing interpretation should be treated as authoritative.

`A10` contains an additional complete 160x96 picture after its normal base and described overlays; the current reconstruction exports it separately.

### F2 architectural graphics

The later corrected F2 interpretation supersedes the initial three-consecutive-set contact sheets.

Unpacked F2 size: `$5F58` bytes.

```text
$0000-$110F   common prefix, $1110 bytes
$1110-$20B7   variant 0, $0FA8 bytes
$20B8-$305F   variant 1, $0FA8 bytes
$3060-$4007   variant 2, $0FA8 bytes
$4008-$4FAF   variant 3, $0FA8 bytes
$4FB0-$5F57   variant 4, $0FA8 bytes
```

The game constructs a `$20B8` graphics extension from:

```text
common prefix                   $1110
first $08F8 bytes from variant A
last  $06B0 bytes from variant B
```

The investigation found selector tables equivalent to:

```text
selector    0 1 2 3 4 5 6 7
variant A   0 1 2 0 3 4 2 0
variant B   0 1 2 0 3 4 4 0
```

Picture dimensions are supplied by descriptor data in F0/F1 rather than stored as another dimension set inside F2. This explains why the original F2 contact sheets degraded as they progressed.

Prefer `generated_resources/legend_graphics/f2_corrected/` over `generated_resources/legend_extracted_stage2/png/PACS/F2/F2_set*.png` and the older `f_probe/` images.

### ANBORD / ANIMBORD

Main component boundaries have been source-derived around a three-plane/template renderer:

```text
$000  16x16  corner
$060  32x16  horizontal border
$120  16x32  vertical border
$1E0  16x16  second corner
$240  32x16  second horizontal border
$300  16x32  second vertical border
$3C0  32x28  panel/artwork
$510-$6E7    control / colour / animation-related data
```

`ANIMBORD` shares the main pixel artwork with `ANBORD`; investigation differences were principally later in the control-data area, with changes not beginning until around `$62C` in the compared outputs.

Prefer `generated_resources/legend_graphics/anbord_solved/ANBORD_components.png`. The earlier `anbord_probe`, `next_probe`, and `known_probe` images are retained only as history.

### WORLD

`WORLD.PAC` decompresses to `$5603` bytes and itself contains nested PAC streams. The game was traced invoking the decompressor at WORLD-relative offsets:

```text
+$0000
+$0380
+$1448
+$2990
```

The first three nested streams were structurally confirmed with unpacked sizes:

```text
+$0000 -> $0500 bytes
+$0380 -> $2678 bytes
+$1448 -> $4880 bytes
```

The fourth stream produces a coherent 32,000-byte 320x200 four-plane world-map screen. Its original stream requires a final byte beyond the nominal end of WORLD. Exhaustive testing during the investigation left two values capable of producing the required 32,000-byte output; `$CE` was selected because it produces a zero/black final bitplane tail rather than the all-one alternative. This repair is deliberate and should remain documented.

Use `generated_resources/legend_extracted_stage3/png/PACS/WORLD/world_map.png` / `_2x.png`.

### Complete raw PAC corpus

`raw_pac/` in this hand-off was regenerated from the original input archive with the verified depacker. It contains all 93 raw decompressed PAC resources and is the preferred starting data for further analysis.

## Strong working interpretations that still merit renderer-level verification

### PARTY

Correct PAC output size is 32,000 bytes. The investigation obtained coherent 320x200 four-plane artwork using the Amiga/ST planar interpretation. The visual result is strong and has not been contradicted by later tracing.

### SPIT M00-M21

Each decompresses to exactly 15,360 bytes and produced coherent 96x320 monster/sprite sheets. The family is strongly graphical.

### TILES2 / TILESX

The working interpretation is 16x8 four-plane, row-interleaved tiles. The intermediate tool reports 355 tiles for TILES2 and 224 for TILESX and produced coherent atlases. These results were not subsequently invalidated, but future work should still bind any editor-facing slicing to the game's exact tile-selection code rather than rely solely on the regular size.

## Partly solved / current research targets

### SPELBITS

Confirmed as a mixed graphics/data resource and a major remaining target.

The investigation found multiple drawing paths where the game selects pointers relative to SPELBITS and sends them to planar renderers. It also found a second renderer using three source planes/template indices.

An embedded PAC begins at `SPELBITS+$5784` and expands to exactly 32,000 bytes. This yielded a coherent full-screen spell-book/background graphic.

Earlier probe work identified boundaries around `$3990` and several apparent four-plane/three-plane graphic groups. Later tracing of the actual object renderer showed that SPELBITS also contains intertwined selector/descriptor information and that some of those early contact sheets were interpreted too quickly. Those sheets remain useful visual evidence, but their individual picture identities/boundaries are not all promoted as final.

The object-rendering path appears component-based:

```text
runtime object record
 -> graphic/component selector
 -> byte sequence of component IDs, terminated/controlled by values such as $FF
 -> component descriptor/pointer data
 -> planar renderer
```

A runtime object table at `$341CE` was identified during the investigation. It consists of four-byte records and is constructed/modified at runtime. This is why a simple static object-to-icon directory was not found directly in the disk image.

Actual inventory/equipment object icons remain unresolved and should be the next source-led target.

### UINV

The old `128x44` whole-image interpretation is superseded.

Known early components are:

```text
$000  16x16 icon
$060  alternate/state version
$0C0  16x16 X/cancel icon
$120  16x16 crossed-swords icon
$180  16x32 diamond/plinth-type graphic
```

The `$280+` region contains coherent structured component data but was not established as the real object-icon bank. The contact sheet named `UINV_objects_17_contact.png` is therefore a probe, not a final object-icon set.

## Known non-image / structured families

### PRUMS/Rxx

Every supplied PRUMS PAC expands to exactly 2,048 bytes. The data is highly structured and looks room/map/resource-like rather than a straightforward bitmap. Do not force these into arbitrary image dimensions.

### SPIT/M80-M87

Each expands to 1,024 bytes. These are not normal M00-M21 monster sheets; examples include structured records and readable text. Earlier image probes are retained as diagnostics only.

## Explicitly superseded / diagnostic outputs

The following are intentionally preserved but must not be treated as final graphics conversions:

- `D.TAP` and `m.tap` full-width/tall raw planar renderings. They were produced before their internal format was properly established and are visually noisy.
- `extra_candidates/` and `candidate_degases/` heuristic DEGAS-header probes.
- original F2 `F2_set1_contact.png`, `F2_set2_contact.png`, `F2_set3_contact.png` interpretation as three consecutive picture sets.
- `f_probe/` arbitrary/sequential F0/F1/F2 layouts.
- `next_probe/`, `known_probe/`, and `anbord_probe/` arbitrary ANBORD dimensions.
- original whole-resource `UINV_128x44` and tile-atlas probes.
- plane-order tests and arbitrary M00 width tests.

These remain in the archive because they document the route to the correct interpretations and can be useful when checking assumptions.
