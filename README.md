# cad-drawing-audit

**Before you batch-parse a folder of DWGs, find out how many of them are actually usable.**

A small audit tool + a real dataset of 21 production drawings, so you can see what
actually breaks in the wild instead of finding out after you've quoted a job.

No dependencies beyond `ezdxf`. No accounts. No API keys.

---

## Why this exists

I ran 21 real mechanical/manufacturing drawings (from a factory, not samples) through
a standard `ezdxf` pipeline.

**Of the 9 drawings that even look like part/BOM drawings, only 2 came out clean.**
The other 19 drawings (of 21) had at least one defect that needed a human before I'd
put the output in front of a customer.

That's not a parsing bug. That's the state of the drawings. If your tool assumes
clean layers and named blocks, it will silently produce a wrong BOM — and it will not
raise an error while doing it.

| What I found | Drawings affected |
|---|---|
| All entities on layer `"0"` (>90%) | **9 / 21 (43%)** |
| Anonymous blocks (`*U54`, `*U55`, ...) | 5 / 21 (24%) |
| Zero text entities (nothing to extract) | 4 / 21 (19%) |
| `名称：` labels stacked on identical coordinates | 3 / 21 (14%) |
| Part drawings with no `数量` (quantity) field | 3 / 21 (14%) |
| Could not be parsed at all | 3 / 21 (14%) |

---

## The failure that matters most: silent wrong answers

Three labels named `名称： ` sat at **exactly** the same coordinates:

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

## What you get

`audit.py <folder>` produces an Excel workbook with three sheets:

1. **Overview** — counts, read failures, entity totals
2. **Per drawing** — one row per file: readable?, entities, text count, layers, blocks, likely type, issues
3. **Issues** — problem types with counts and percentages

---

## Usage

```bash
pip install ezdxf openpyxl
python audit.py /path/to/dxf/folder -o report.xlsx
```

DWG input: run `libredwg`'s `dwg2dxf` first — see [`docs/dwg-conversion.md`](docs/dwg-conversion.md).
That path has its own failure modes and this tool reports them rather than hiding them.

---

## The dataset

`data/drawing_audit_21.csv` — the full audit of all 21 drawings, one row per file,
**anonymized** (file names normalized to `SOURCE*`, no customer names, no part numbers).

It's here so you can check my numbers instead of trusting them. Every count in the
table above maps to a row in that CSV.

**On the count of 21:** that's 27 files deduplicated to 21 by MD5. MD5 proves the *files*
are identical, not that the *drawings* are distinct — see
[`docs/known-failures.md`](docs/known-failures.md). Two of the rows are probably the
same drawing converted twice.

---

## What this does NOT do

- It does **not** convert DWG. Use `dwg2dxf` (libredwg) or ODA File Converter.
- It does **not** guess missing data. Fields it can't verify are marked unverified.
- It does **not** promise a clean BOM. On this dataset only 2 of 21 drawings were clean
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

## License

MIT for the code. The dataset is CC0.


---

## Reproduce these numbers yourself

The 21-drawing result is not a claim you have to take on faith. Run this:

```python
import ezdxf, glob, hashlib

seen, uniq = set(), []
for f in sorted(glob.glob("*.dxf")):
    h = hashlib.md5(open(f, "rb").read()).hexdigest()
    if h not in seen:
        seen.add(h)
        uniq.append(f)
ok = fail = total = 0
for f in uniq:
    try:
        doc = ezdxf.readfile(f)
        total += len(list(doc.modelspace()))
        ok += 1
    except Exception:
        fail += 1

print(len(uniq), "unique /", ok, "readable /", fail, "failed /", total, "entities")
```

Expected on the same 27 source files:

```
21 unique / 18 readable / 3 failed / 151048 entities
```
Two things matter here:

- **The dedup step**: 27 files collapse to 21 unique by MD5. Six of them are the
  same drawing saved twice. Skip dedup and every count downstream is inflated.
- **"Failed" is not "empty"**: 3 files raise on read. They are counted separately
  from drawings that open fine but contain no text. Merging those two categories
  is how you end up telling a customer their good drawing is blank.
`data/drawing_audit_21.csv` has one row per unique file -- that is the number
you should trust without checking.

The full `audit.py` (which also classifies drawing type, finds anonymous blocks,
and detects stacked name anchors) is **not in this repo yet**. I could not push
it through the web editor. The snippet above reproduces the headline counts;
it does not reproduce the per-file issue classification.
