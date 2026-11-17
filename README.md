# cad-drawing-audit

**Before you batch-parse a folder of DWGs, find out how many of them are actually usable.**

A small audit tool + a real dataset of 24 production drawings, so you can see what
actually breaks in the wild instead of finding out after you've quoted a job.

No dependencies beyond `ezdxf`. No accounts. No API keys.

---

## Why this exists

I ran 24 real mechanical/manufacturing drawings (from a factory, not samples) through
a standard `ezdxf` pipeline.

**6 of them were clean. The other 18 had at least one defect that needed a human
before I'd put the output in front of a customer.**

That's not a parsing bug. That's the state of the drawings. If your tool assumes
clean layers and named blocks, it will silently produce a wrong BOM — and it will not
raise an error while doing it.

| What I found | Drawings affected |
|---|---|
| All entities on layer `"0"` (>90%) | **11 / 24 (46%)** |
| Anonymous blocks (`*U54`, `*U55`, ...) | 8 / 24 (33%) |
| Zero text entities (nothing to extract) | 4 / 24 (17%) |
| `名称：` labels stacked on identical coordinates | 6 / 24 (25%) |
| Defined multiple layers but used only one | 10 / 24 (42%) |
| Has text but no `数量` (quantity) field | **11 / 20 (55%)** |
| Could not be parsed at all | **0 / 24 (0%)** |

The worst single file has **503 anonymous blocks** (`*U12`, `*U54`, ...) — a purchaser
reading the BOM literally cannot name the part.

---

## The failure that matters most: silent wrong answers

Several labels named `名称： ` sat at **exactly** the same coordinates:

```
'名称： '   x=  55.0  y= 932.4
'名称： '   x=  55.0  y= 932.4
'名称： '   x=  55.0  y= 932.4
```

Three different parts share one label anchor point. Any code that maps "text nearest
to a geometry point" returns **one** name for three parts. **It does not throw.**
The BOM comes out with a part silently missing, or three parts collapsed into one.

If you're quoting from that output, the quote is wrong and you won't know until the
customer rejects the parts.

`audit.py` flags this case instead of guessing. Pairing offset is written into the
output so a human can re-check it.

---

## How drawings are graded

This is the exact rule set, so you can disagree with it precisely.

**Check in order, stop at first match:**

| Grade | Condition |
|---|---|
| `unreadable` | `ezdxf.readfile()` raises |
| `empty` | `entities == 0` |
| `no_text` | `texts == 0` — nothing to extract, cannot build a BOM |
| `defect` | any of the four below |
| `clean` | none of the above |

**The four defect criteria:**

1. More than **90%** of entities sit on layer `"0"`
2. **≥1** anonymous block (`*`-prefixed name)
3. **≥1** place where two or more `TEXT`/`MTEXT` labels share identical coordinates
4. `layers_used <= 1` while `layers_defined > 1`

**Deliberately NOT a defect:** a missing `数量` field. Some drawings are assemblies,
not part lists; absence of a quantity column is normal there. It is reported as its
own column (`qty_hits`) rather than folded into the grade.

---

## What you get

`audit.py <folder>` produces an Excel workbook with three sheets:

1. **Overview** — counts, read failures, entity totals, zero-text and unclassified counts
2. **Per drawing** — one row per file: readable?, entities, text count, layers, blocks, likely type, issues
3. **Issues** — problem types with counts and percentages

---

## Usage

```bash
pip install ezdxf openpyxl
python audit.py /path/to/dxf/folder -o report.xlsx
```

> **`audit.py` is not in this repo yet.** The three sheets above are the exact output
> from running it on the dataset described here. The script is being uploaded separately;
> open an issue if you want it before then and I'll paste it inline.

### DWG input

Two paths, and the difference matters:

| Path | Success on this dataset | Note |
|---|---|---|
| **AutoCAD COM** (`Documents.Open` + `SaveAs` with DXF code 61) | **26 / 27** | Requires local AutoCAD. Most reliable. |
| `libredwg`'s `dwg2dxf` | ~1 / 15 | Fails with `Skip HATCH common handles due to short handle stream`. |

**An earlier version of this dataset was built with `dwg2dxf`, and 3 files
"could not be parsed at all." Those same 3 files open fine through AutoCAD COM.**
The 0% parse-failure rate above is the AutoCAD path.

If you only have `dwg2dxf`, this tool still reports which files it couldn't read —
it just won't be zero.

---

## The dataset

[`data/drawing_audit_25.csv`](data/drawing_audit_25.csv) — one row per drawing,
**anonymized** (file names normalized, no customer names, no part numbers).

It's here so you can check my numbers instead of trusting them. Every count in the
table above maps to a row in that CSV.

**How 24 was reached:** 26 DXF files came out of AutoCAD, 1 was an intermediate
artifact I generated myself (`_minimal.dxf`), and the remaining 25 deduplicated to
**24 unique drawings by MD5**. MD5 proves the *files* are identical; two rows that
hash differently might still be the same drawing exported twice.

---

## What this does NOT do

- It does **not** convert DWG. Use AutoCAD COM (preferred) or `dwg2dxf` / ODA File Converter.
- It does **not** guess missing data. Fields it can't verify are marked `待确认` / unverified.
- It does **not** promise a clean BOM. On this dataset only 6 of 24 drawings were clean
  enough to use as-is. That's the point.

---

## Why I built it

I'm a mechanical/electrical automation guy in Zibo, China (kiln and furnace control
systems) who kept getting handed folders of drawings where "just extract the BOM"
turned into three days of manual correction. This is the checklist I now run *before*
quoting.

If you have a folder of drawings and want to know which ones are salvageable before
you commit to a job, open an issue with a sample — I'll run it and tell you what's
wrong with it, including if the answer is "your drawings are fine, my tool is wrong."

---

## Corrections

**2026-11-17** — Numbers revised from 21 drawings to 24. Three specific errors:

| Claim (before) | Corrected | Why |
|---|---|---|
| "only 2 of 21 drawings were clean" | **6 of 24** | Earlier version used `dwg2dxf` output where 3 files failed to parse |
| "could not be parsed at all: 3 / 21 (14%)" | **0 / 24** | Those 3 were a converter artifact, not a drawing defect |
| "no 数量 field: 3 / 21 (14%)" | **11 / 20 (55%)** | Old check only read modelspace `TEXT`, missing `MTEXT` and block `ATTDEF` |

The last one went the wrong way: the real number is much worse than first published.

**Also fixed:** the grading rules above are now written down and applied by a single
script. Before this, three different implementations of "is this drawing clean?"
produced 0, 6, and 7 on the same folder.

---

## License

MIT for the code. The dataset is CC0.
