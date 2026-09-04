# Complete investigation notes

## Scope and input treatment

The source material was an archive of the Amiga version of *Legend / Four Crystals of Trazere* by the Bloodwych author. The investigation began with no assumption about which files held graphics. All `.uaem` files were identified as emulator metadata and excluded from format analysis.

The original archive is not copied into this generated-output bundle. See `SOURCE_PROVENANCE.md` for its checksum.

## 1. Initial file inventory and first graphics identifications

The extracted game contained meaningful files under `C`, `PACS`, `SPIT`, and `PRUMS`.

The strongest graphics candidates from names alone were in `PACS`, including:

- `TILES2.PAC`
- `TILESX.PAC`
- `PARTY.PAC`
- `ANBORD.PAC`
- `ANIMBORD.PAC`
- `UINV.PAC`
- `WORLD.PAC`
- `spelbits.pac`
- `A00.PAC` through `A10.PAC`
- `F0.PAC`, `F1.PAC`, `F2.PAC`

`SPIT/M00.PAC` through the later Mxx family were also immediately suspicious as monster/sprite resources.

The executable `C/leggo` contains literal references to several of these PAC names, which established that these are genuine runtime resources rather than unrelated data.

`C/4XEUR` and `C/BEUR` were the first completely solved pictures. Both begin with the DEGAS Elite compressed low-resolution marker `$8000`, followed by a 16-word Atari ST palette. PackBits-style DEGAS decompression yielded complete 320x200, 16-colour screens. These are retained as native and 2x PNGs.

This demonstrated that Atari-ST-style planar graphics heritage was relevant even though the supplied game build is Amiga.

`C/D.TAP` and `C/m.tap` also begin with plausible 16-colour words, but treating their remaining bytes as a simple sequence of ordinary 320-pixel four-plane rows produced noisy images. Those outputs were retained only as diagnostic probes.

`PACS/DT.BIN` and `PACS/NT.BIN`, and corresponding files in `C`, contain 68000 code and are not ordinary picture files.

## 2. PAC container mapping

Before the decompressor itself was solved, every PAC showed a consistent outer structure. The file could be partitioned exactly into one or more blocks with:

- a continuation/rule count field,
- a compressed payload count,
- three equal-size byte tables,
- compressed payload bytes.

This allowed every PAC block boundary to be mapped without guessing graphics dimensions.

The eventual code tracing in `C/leggo` confirmed the exact format and the reverse substitution order. See `PAC_FORMAT.md` for the definitive description.

All supplied PAC files now parse exactly: 93 PAC resources, 296 compression blocks.

## 3. PAC decompression result families

Correct decompression exposed strong fixed-size families:

- `PARTY.PAC` -> 32,000 bytes.
- `SPIT/M00-M21` -> 15,360 bytes each.
- all supplied `PRUMS/Rxx` -> 2,048 bytes each.
- `SPIT/M80-M87` -> 1,024 bytes each.

These regular sizes were a critical validation of the algorithm.

A second reference expansion matching the original staged 68000 semantics was compared with the simpler reverse-order byte replacement implementation during the investigation; the outputs matched across the supplied blocks.

The corrected byte-pair order is `key -> table3, table2`. An earlier experimental `table2, table3` ordering could make graphics look close while retaining corruption and was discarded.

## 4. Early graphical PAC outputs

After PAC decompression:

### PARTY

`PARTY.PAC` produced a coherent 320x200 four-plane party/character image. Plane-order experiments were retained in the historical outputs.

### SPIT M00-M21

The fixed 15,360-byte resources produced coherent 96x320 monster/sprite sheets. Arbitrary alternative dimensions such as 256x120 were tested during diagnosis and retained as probes, but the coherent family result is 96x320.

### TILES2 and TILESX

A 16x8, four-plane, row-interleaved tile interpretation produced coherent tile atlases. The intermediate extractor records 355 tiles for TILES2 and 224 for TILESX.

### UINV

An early whole-resource 128x44 interpretation looked plausible enough to be useful diagnostically but was later superseded by source-led component boundaries. It must not be used as the final UINV format.

### PRUMS and M80-M87

Attempts to force these small fixed-size resources into pictures showed that they are structured data rather than normal bitmap families. The M80 family also exposed readable text/records after correct decompression.

## 5. Shift to source-led geometry

The most important methodological correction came when later F2 contact sheets looked progressively worse. This showed that a byte count being factorable into an attractive rectangle was not enough evidence.

From that point onward, final dimensions were accepted only when supported by one of:

- an explicit resource offset table,
- dimension fields used by the 68000 renderer,
- exact successive-offset arithmetic,
- or a full-screen fixed-size destination known from the game code.

Historical arbitrary-dimension images are retained for traceability but explicitly marked as superseded.

## 6. F0/F1/F2 architecture and corrected F2 model

The initial interpretation treated F2 as three consecutive graphic sets. The first contact sheet looked strong and later pictures degraded. Source tracing showed why.

Unpacked F2 is `$5F58` bytes with a `$1110` common prefix followed by five `$0FA8` variants:

```text
$0000-$110F common prefix
$1110-$20B7 variant 0
$20B8-$305F variant 1
$3060-$4007 variant 2
$4008-$4FAF variant 3
$4FB0-$5F57 variant 4
```

At runtime the game assembles an extension using the common prefix plus portions selected from two variants:

```text
$1110 common
$08F8 from variant A
$06B0 from variant B
= $20B8
```

The selector mappings found during the investigation were:

```text
selector    0 1 2 3 4 5 6 7
variant A   0 1 2 0 3 4 2 0
variant B   0 1 2 0 3 4 4 0
```

The actual picture dimensions are not another sequential table in F2. F0/F1 supply descriptor data. The renderer reads fields equivalent to width-in-16-pixel-words-minus-one and height-minus-one, with additional placement/render bytes.

This corrected the progressive loss of synchronisation in the first F2 contact sheets.

## 7. ANBORD and ANIMBORD

Initial arbitrary renders suggested the data was graphical but the dimensions were not stable.

Code tracing established internal graphics boundaries consistent with the game's three-plane/template renderer:

```text
$000  16x16
$060  32x16
$120  16x32
$1E0  16x16
$240  32x16
$300  16x32
$3C0  32x28
$510+ control/colour/animation data
```

The resource therefore combines artwork and non-pixel control data.

`ANIMBORD` shares the principal artwork with `ANBORD`; differences were observed only later in the control-data area, beginning around `$62C` in the compared resources.

## 8. Hard-coded palettes

The earliest PAC renders used the colour words at the beginning of `D.TAP` simply as a working palette. This made structural checking possible but did not match the game appearance.

Subsequent executable tracing found gameplay palettes hard-coded in `C/leggo`. The principal palette used for the corrected scene contact sheet was tracked with the investigation offset/label `0x1D6D6`. Two other palette probes were retained under labels `0x3E5A6` and `0x3E5C6`.

The main hard-coded palette gave a much more convincing normal-game appearance to Axx scenes. The exact 16 words used for the current regenerated Axx assets are written to `reconstructed_current/scenes/gameplay_palette_main_0x1D6D6.tsv`.

Some renderers, especially three-plane/template artwork, can remap source indices dynamically. A source bitmap can therefore have correct geometry while a static palette still does not exactly reproduce every in-game circumstance.

## 9. A00-A10 location/encounter scenes

These became one of the strongest structured-resource results.

Each Axx decompressed resource begins with a small header containing offsets to internal tables. The relevant current reconstruction identifies:

- an overlay descriptor table,
- a 32-entry animation-sequence pointer table,
- a graphics-offset table,
- and a graphics-data base.

The graphics-offset table's first values are consistently:

```text
$0000  base picture
$1E00  first overlay
```

The base picture is exactly 160x96 at four bits per pixel:

```text
160 * 96 * 4 bits = 7,680 bytes = $1E00
```

Overlay descriptor records are four words:

```text
width_in_16_pixel_words - 1
height - 1
screen X
screen Y
```

For nearly all overlay records, the calculated byte size exactly equals the distance between consecutive graphics offsets. This provides strong internal validation independent of the visual output.

The number of overlays varies substantially by scene: examples found during the investigation include A00 with 24 overlays, A01 with 29, A07 with 57, and A10 with 12 normal overlays.

A10 contains an additional full `$1E00` 160x96 scene after its normal overlay data. This explains the earlier accidental-looking 160x192 interpretation.

The animation table has 32 relative pointers. Each pointer selects an exact byte sequence. Sequences contain overlay numbers and control values. Examples include simple frame progressions and longer cycles. Values in `$80-$8F` appear as control commands, but their exact timing/control meanings are not yet final.

For this hand-off, all 17 Axx resources were regenerated from the decompressed raw bytes using their own offset and descriptor tables. `reconstructed_current/scenes/` therefore contains:

- native and 2x base PNGs,
- every described overlay as native and 2x PNG,
- each overlay composited at its source-defined X/Y onto the base scene,
- `overlays.tsv` with exact dimensions/positions/offsets,
- `animation_sequences.tsv` preserving all 32 sequences byte-for-byte,
- additional complete scenes where detected, including A10,
- a current scene-base contact sheet.

This regenerated set is intended to replace inaccessible directory links from earlier turns.

## 10. SPELBITS

SPELBITS remains a large mixed resource and a priority target.

The investigation found multiple code paths that compute pointers relative to SPELBITS and send them into planar graphics routines. It therefore unquestionably contains substantial artwork, but it also contains selectors, tables and other structured data.

### Three-plane/template rendering

A renderer was identified that consumes three 16-bit source planes per 16 pixels, six bytes rather than eight. Those three source bits are mapped into the final four Amiga screen planes at draw time. This explained several previously puzzling exact byte strides.

For example, a 16x14, three-plane source consumes:

```text
16 * 14 * 3 bits = 84 bytes = $54
```

The game indexes one discovered group at `$54` intervals.

Earlier contact sheets show recognisable rune/symbol-like groups using this interpretation. Their geometry is useful evidence, but exact final colour remapping remains context-dependent.

### Embedded PAC

At `SPELBITS+$5784`, the game passes the data to the same PAC decompressor again. The nested stream expands to exactly 32,000 bytes and yielded a coherent 320x200 four-plane spell-book/background screen.

This nested-PAC discovery is retained as a strong result.

### Object icon path and later correction

The investigation initially interpreted several earlier SPELBITS ranges as sequences of ordinary raw graphics based on visual output. Later disassembly of the object renderer showed the resource also contains intertwined selector/descriptor information.

The object graphics path appears to use:

- a runtime object record,
- object/graphic selector information,
- a byte sequence of component IDs,
- descriptor/pointer data for each component,
- the normal planar renderer.

A runtime object table was identified at `$341CE`. It contains four-byte records and is populated or modified during game setup. This explains why the static on-disk bytes did not yield a simple final object-icon directory.

Therefore the actual sword/dagger/staff/shield/potion/etc. object-icon atlas is **not yet solved**. The existing SPELBITS contact sheets are preserved as investigation probes, not asserted as final per-object boundaries.

## 11. UINV

The early whole-resource 128x44 picture interpretation was rejected after source-led component analysis.

Current established early components are:

```text
$000  16x16 icon
$060  alternate/state version
$0C0  16x16 X/cancel icon
$120  16x16 crossed-swords icon
$180  16x32 diamond/plinth-type graphic
```

The remaining `$280+` region contains coherent UI/slot/plinth-type structure but was not demonstrated to be the game's actual item icons. The historical `UINV_objects_17_contact.png` is included exactly as a probe and must not be relabelled as a final inventory-object sheet.

## 12. WORLD

The outer WORLD PAC expands to `$5603` bytes.

Code tracing showed that WORLD contains nested PAC streams and explicitly invokes the depacker at WORLD-relative offsets:

```text
$0000
$0380
$1448
$2990
```

The first three nested outputs were established as:

```text
$0000 -> $0500 bytes
$0380 -> $2678 bytes
$1448 -> $4880 bytes
```

The `$2990` stream is used as a full-screen graphics source. Parsing it from the nominal WORLD boundary requires one additional byte beyond the resource end. Exhaustive testing found only two values that yield the expected 32,000-byte decompressed size. `$CE` was selected for the reconstructed image because it yields a zero/black final bitplane tail rather than the all-one alternative.

The resulting world map is visually coherent and retained in `generated_resources/legend_extracted_stage3/png/PACS/WORLD/`.

The first three WORLD nested resources remain open for further format identification.

## 13. Historical probes retained intentionally

A large set of experiments is included rather than discarded. These document false starts and are useful for regression checking:

- DEGAS candidate scans inside executable/data files.
- D.TAP and m.tap tall/page interpretations.
- plane-major vs row-interleaved tests.
- M00 alternative width probes.
- PARTY plane-order tests.
- TILES2/TILESX arbitrary sheet/atlas tests.
- UINV whole-image and tile probes.
- F0/F1 sequential and arbitrary-width probes.
- original incorrect F2 consecutive-set contact sheets.
- multiple ANBORD arbitrary-dimension probes.
- initial A00 head/tail and large-sheet probes.
- first SPELBITS width/contact interpretations.
- WORLD arbitrary-width probes.

They are not deleted because the user's explicit requirement is to preserve the entire investigation output as a continuation resource.

## 14. Tooling state

The thread produced `legend_graphics_extract.py`, preserved here as `tools/legend_graphics_extract_intermediate.py`.

Its PAC decompressor is valuable and correct. Some embedded image-layout recipes are now stale, particularly:

- `UINV.PAC` as one 128x44 plane-major bitmap;
- using `C/D.TAP` as the default general gameplay palette.

For that reason this consolidation also contains `tools/legend_pac_decompress.py`, a clean standalone PAC parser/decompressor with no graphics assumptions. Future development should start from that verified core and add source-backed renderers one family at a time.

## 15. External contextual reference

A 2017 encode.su discussion concerned the same Legend PAC family and suggested reversing the DOS release's `LEGPIC.EXE`. It did not provide the final algorithm used here. The actual PAC solution in this investigation came from the supplied Amiga resources and tracing the game's 68000 loader.

Reference retained for context:

https://encode.su/threads/2773-Help-on-identifying-DOS-file-encryption-packer

## 16. Recommended continuation order

1. Finish the runtime object-record / SPELBITS component directory and render authoritative inventory/equipment object icons.
2. Decode the `$80-$8F` Axx animation control commands and timing, then generate source-faithful animated scene previews.
3. Finish context-dependent palette/template remapping for three-plane SPELBITS and ANBORD artwork.
4. Identify the first three nested WORLD outputs at `$0000`, `$0380`, and `$1448`.
5. Bind TILES2/TILESX and monster/party slicing to exact game selector tables for editor-grade round-tripping.
6. Update the all-in-one graphics extraction tool only after these source-backed formats have been incorporated, retaining the PAC core unchanged.
