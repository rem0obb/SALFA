# FLARE / JLR Gen21 algorithm

The verifier is in `108_00D23000_MIUT_WPR.BIN` and the hash implementation is
in `009_0046D000_MIUT_SLIB.BIN`.

## Recovered input

The verifier constructs exactly 197 bytes:

1. 20 ASCII bytes: `FiE_Gen21_NAVI_00_` plus the two-letter region.
2. 17 VIN bytes. The receiver unconditionally changes the first byte to `S`.
3. The first 160 bytes of `UPDATE.INF` on the DVD/USB, read at offset 0.

It computes standard SHA-1 over those bytes and returns the XOR of the five
big-endian 32-bit digest words. The displayed code is that value as eight
uppercase hexadecimal digits.

```text
digest = SHA1(product[20] || vin[17] || UPDATE.INF[0:160])
code   = digest.word0 XOR digest.word1 XOR digest.word2
         XOR digest.word3 XOR digest.word4
```

## Relevant addresses

- WPR `0x41503A88`: builds the 197-byte message and compares the code.
- WPR `0x4150D150`: receives 17 VIN bytes and forces byte zero to `S`.
- WPR `0x4150426C`: parses exactly eight hexadecimal code digits.
- SLIB `0x304235AC`: copies 20 + 17 + 160 bytes and calls the hash.
- SLIB `0x3042365C`: standard SHA-1 and XOR-folded return value.

The module linkage was verified directly from the export tables. SLIB export
table index `0x1E2` (table byte offset `0x7F0`) contains `0x304235AC`, exactly
the ordinal invoked by the WPR stub at `0x4150D870`. FILE export index `0x12`
contains `0x30602FE0`; this function forwards its `a2` argument unchanged as
the raw read length. WPR passes `a2 = 0xA0` and does not seek before that read.

As an independent execution check, the actual little-endian MIPS SLIB module
was run under Unicorn with the 197-byte EU messages built from the supplied
`ALLDATA.KWI`. The machine code returned `873D3A23` and `7F783996`, exactly
matching the Python implementation. This rules out an inferred SHA variant,
word-order mistake, or output-format mistake.

The region field at WPR `0x72202D4E` is a bit mask. The complete dispatch is:

```text
0x001 JP   0x002 EU   0x004 US   0x008 PA
0x010 CN   0x020 KR   0x040 TW   0x080 ME
0x100 RU   0x200 ZA   0x400 SA   0x800 SE
```

WPR copies only the first 20 bytes of the selected 24-byte constant, so no
terminating zero is included. Its hexadecimal parser accumulates the eight
entered nibbles from most significant to least significant and compares the
resulting normal 32-bit value directly with the SLIB result. There is no byte
swap or alternate display encoding missing from the generator.

The filename reaches WPR through shared memory at `0x72202974`. WPR
concatenates it with the selected DVD/USB root, opens that file, and reads 160
bytes from offset zero. Analysis of the producer later established that the
activation path fixes this filename to `UPDATE.INF`.

The complete shared object is 0x20C bytes and is synchronized at external
address `0xE3B0000C`. WPR imports it at `0x41504E40`/`0x41504E8C`; the code
generator later consumes its filename at `0x41503B34`. Other WPR paths use the
same value while processing the update. Nearby hard-coded strings identify
other update paths such as `ALLDATA.KWI`, `MUINFDVD.BIN`, and `Mapinfo.txt`;
they are unrelated to the 160-byte activation input.

At `0x41502020`, WPR copies 0x100 bytes from offset 0x110 of an incoming update
message into `0x72202974`. The following 0x100-byte field and status words
complete the 0x20C-byte current-file record. WPR's media-root helper selects
`/iedvd/` or `/ieusb/slot...`; its open/read wrappers perform an ordinary raw
open and 0xA0-byte read, without decrypting or decompressing the bytes first.

## UPDATE.INF producer path

The CARDFS module from flash offset `0x612000` runs at `0x3A5F1000`. Its event
dispatcher at `0x3A604358` creates a 0x210-byte message and dispatches operation
types 0 through 20. Type `0x10` calls `0x3A608C78` through the jump-table target
at `0x3A6046E0`.

That function copies the 11 literal bytes `UPDATE.INF` from `0x3A613510` into
message offset `0x10`, then copies that resulting name into message offset
`0x110`. The dispatcher sends the complete message as event `0x2515` at
`0x3A60470C`.

WPR receives that event, copies message offset `0x110` to `0x72202974`, and
dispatches the message status. Its 22-entry jump table at `0x41502CF8` maps
status `0x10` to `0x41502D50`. This handler sets the third readiness flag and
calls `0x415039F4`; once all three flags are set, it invokes the generator at
`0x41503A88`.

Inside the generator, WPR joins the selected media root with `UPDATE.INF`,
opens it at `0x41503B48`, and at `0x41503B94` requests exactly `0xA0` bytes into
the hash input buffer. No seek, parsing, decryption, or decompression occurs.
The exact external input is therefore:

```text
UPDATE.INF[0:160]
```

The `UPDATE.INF` filename strings found in `LOADING.KWI` and the flash dump are
part of CARDFS executable code. They are not the contents of the external file.

The subsequently supplied `UPDATE.INF` is exactly 160 bytes and has SHA-256
`9ec7d487ee8b98b1b895045336aca92fac9595736606e1e9a135a6ffd8125663`.
Using it with region `EU` reproduces both known-answer pairs exactly:

```text
SALFA2AEXEH401960 -> 2A8AD051
SALFA2AE8DH343605 -> 2921B711
```

These bytes are bundled as the generator's default CTF profile. An external
`UPDATE.INF` is only needed when generating codes for a different update media.

The two supplied VIN/code examples cannot recover that 160-byte value: it is
SHA-1 input, not a value embedded in this verifier. Both examples were checked
together against every 160-byte window in every file currently in this folder,
all 12 regional prefixes, and the first 160 decompressed bytes of every member
of `qnx_extracted.zip`. None reproduces both `2A8AD051` and `2921B711`.

The similarly named files do not provide an alternate VIN-only implementation:

- `Algo_should_be_here` is the `SS_PLAYER` audio/CDDB module.
- `VINW` and `VINR` in `LOADING_3.kwi` are AVC/VICS communication commands.
- `LOADING.kwi`, `LOADING_2.kwi`, `LOADING_3.kwi`, and `LOADING_4.kwi` are
  different platform/firmware generations and do not contain the Gen21 region
  strings used by this verifier.

Consequently, the VIN-and-region-only program bundles the first 160 bytes of
the challenge's exact `UPDATE.INF`. Those bytes could not have been derived
from two 32-bit SHA-1 results; they were taken from the subsequently supplied
file rather than inferred or replaced with hardcoded example outputs.

## Flash dump validation

The later `S29GL512SxxTFxV1@TSOP56 CHIP 1.BIN` is a 64 MiB Gen21 program
flash dump. `S29GL512SxxTFxV1@TSOP56_CHIP_1_splits.zip` contains 51 named
segments; every extracted segment is byte-identical to the corresponding BIN
offset, so it adds labels but no additional data.

The relevant installed modules are unchanged:

- Flash `WPR` at `0x90D000`, first 64 KiB SHA-256
  `be92ab4e161061eba62a439453e7054bb49fa557e2ac6ce2e1253aac4a1ea156`,
  is identical to `LOADING.KWI` offset `0xD23000`.
- Flash `SLIB` at `0x057000`, size `0x3A000`, is identical to
  `LOADING.KWI` offset `0x46D000`.
- Flash `FILE` has the same archive CRC (`690053D7`) as the KWI module.

An exhaustive scanner tested every possible 160-byte window of the complete
flash dump for every one of the 12 region prefixes. This covered 67,108,961
windows per region (805,307,532 window/region combinations). No window even
reproduced the first supplied result `2A8AD051`; therefore none can reproduce
both examples. The expected codes also do not occur as big- or little-endian
32-bit constants in the dump.

This flash contains the verifier implementation but not the external
`UPDATE.INF`. It therefore confirms the recovered algorithm while also
confirming that the external 160-byte input is not stored in the firmware
artifacts.

The files named `LOADING*.KWI` are firmware/update containers, and the 64 MiB
BIN is installed program flash. Testing their first 160 bytes does not produce
either supplied example for any region. The separately supplied `UPDATE.INF`
is the input identified by both the code path and the known-answer tests.

## Supplied ALLDATA.KWI

The later `ALLDATA.KWI` is a 4096-byte European update index. Its SHA-256 is
`b3c2d6cc6d1cd3ebf60485175a3e2ce3572f0d94bd4737eb48e0afba86dcb642`, and
its metadata contains `AEU_12_202101A` and `DATA VERSION 21/10/14/01`. It
enumerates payloads including `PARCEL.KWI`, `REGION.KWI`, `INDEXDAT.KWI`, and
`PARAM.KWI`, but those payload files are not present in this folder.

Using this file's actual first 160 bytes with the EU prefix produces:

```text
SALFA2AEXEH401960 -> 873D3A23
SALFA2AE8DH343605 -> 7F783996
```

All 3,937 possible 160-byte windows in the file were additionally checked
against all 12 region prefixes. None reproduces even the first expected code
`2A8AD051`. Thus this particular `ALLDATA.KWI` is not the runtime payload used
to produce the supplied known-answer pairs.

## KIWI tools supplied later

The `downloads/Kiwi_src_0.0.4` directory contains source for generic KIWI 1.22
readers, builders, and compression tools. Its `AllDataManagementFrameType`
parser confirms that an `ALLDATA.KWI` management frame is exactly 4096 bytes:
a 2048-byte data volume followed by a 2048-byte management-record sequence.
Therefore the supplied 4096-byte file is complete, rather than a truncated
copy whose missing tail might contain the generator input.

Decoding its 18-byte management records as Denso DSAs gives these external
files, among others:

```text
record  1  PARCEL.KWI    0x583 sectors
record  2  REGION.KWI    0x005 sectors
record  3  INDEXDAT.KWI  0x004 sectors
record  4  PARAM.KWI     external/absent
record  7  VOICE002.ME   0x001 sectors
record 34  VOICE001.ME   0x037 sectors
record 35  PAR_MNG.ME    0x584 sectors
record 40  PATTERN.ME    0x001 sectors
record 41  LOADING.KWI
record 42  TMCINFO.ME    0x03E sectors
record 43  VOICE003.ME   external/absent
```

These names are references; their contents are not embedded in the 4 KiB
management frame. The newly supplied directory contains 71 source/tool files
totalling 1,650,945 bytes and none of the referenced map payloads. Every
possible 160-byte window in all 71 files was tested with both supplied VINs
and all 12 region prefixes. No window reproduces `2A8AD051`, so the utilities
themselves do not contain the `UPDATE.INF` seed either.
