# Legend PAC compression format

## Status

The `.PAC` container/decompression layer is considered solved for the supplied game set.

All 93 supplied PAC files parse to exact file boundaries and contain 296 compression blocks in total. A second, stage-aware reference implementation matching the 68000 loader semantics was compared with the simpler reverse-substitution implementation during the investigation; the outputs agreed across the supplied blocks.

## Block structure

All multi-byte integer fields are big-endian.

```text
word 0:
    bit 15       continuation flag: another compressed block follows
    bits 14..0   rule_count - 1

word 1:
    compressed payload byte count - 1

then:
    key[rule_count]
    table2[rule_count]
    table3[rule_count]
    payload[payload_size]
```

The stored `-1` values match the original 68000 loader's DBRA/DBF terminal-count handling.

## Rule expansion

For rule index `i`, the original game expands:

```text
key[i] -> table3[i], table2[i]
```

The rules are staged substitutions and therefore have to be undone in reverse creation order:

```python
buf = payload
for i in range(rule_count - 1, -1, -1):
    buf = buf.replace(bytes([key[i]]), bytes([table3[i], table2[i]]))
```

Each expanded block is concatenated in file order.

The third-table-before-second-table order is important. An earlier experimental decoder used the opposite order and produced artwork that could look nearly correct while retaining corruption. Tracing the game loader resolved this.

## Strong size checks produced by the correct algorithm

Examples from the supplied resources:

- `PARTY.PAC` -> exactly 32,000 bytes.
- `SPIT/M00.PAC` through `SPIT/M21.PAC` -> exactly 15,360 bytes each.
- every supplied `PRUMS/Rxx.PAC` -> exactly 2,048 bytes.
- `SPIT/M80.PAC` through `SPIT/M87.PAC` -> exactly 1,024 bytes each.

These regular fixed-size families emerge only after correct decompression and provided useful validation alongside the 68000 source path.

## Reference implementation

Use `tools/legend_pac_decompress.py`. It deliberately does not contain any image-size or palette assumptions.
