# DWG to DXF: what actually breaks

`audit.py` reads DXF only. `ezdxf` cannot open native DWG (binary) files - it is a DXF
library, not a DWG library. If you point it at a `.dwg` you get an error, and if you
assume that error means "the file is corrupt" you will be wrong about a file that opens
fine in AutoCAD.

This page is the conversion path I actually used, including its failure rates.

---

## Option 1: libredwg (dwg2dxf)

Free, open source, no account.

```bash
# Windows: grab the win64 build
# https://github.com/LibreDWG/libredwg/releases/download/0.14/libredwg-0.14-win64.zip
dwg2dxf --as r2018 -o output.dxf input.dwg
```

**Read the official claim carefully:**

> `dwg2dxf -- Converts a DWG to a DXF... **About 90% coverage.**`

"About 90% coverage" is not "about 90% of your files". It is coverage of the DWG format
surface. My result below is the practical version of that sentence.

### My measured result (27 files, Nov 2026)

```
files to convert : 27
converted OK     : 26 / 27
parseable after  : 22 / 27
entities read    : 214,550
```

The five failures:

| File class | Error | Cause |
|---|---|---|
| One file | `Invalid handle 0.` | object handle graph broken in source DWG |
| Two files >80 MB | `Invalid binary data near line: 3811398.` | libredwg hits a section it cannot walk at that size |

**So: 26/27 convert, 22/27 are usable.** That gap - 4 files that convert but still will not
parse - is the part nobody mentions.

## Option 2: ODA File Converter

Free (registration required), official, from the Open Design Alliance.
Title on their own page: *"ODA DWG-DXF CONVERTER For converting between different
versions of .dwg and .dxf"*.

Better on large and modern files. Costs a signup, which is why I used libredwg first.

## Option 3: AutoCAD COM automation

Windows + a licensed AutoCAD install. Highest fidelity by far, because it is Autodesk's
own reader. Not viable for headless use.

---

## The trap: "converted" is not "readable"

A successful `dwg2dxf` exit code tells you a file was written. It does not tell you the
DXF is complete. Two things bite immediately:

1. **Text arrives with MTEXT formatting codes baked in.** Labels come out as
   `{\fSimSun|b0|i0|c134|p2;\H0.83333x;名称：}`, not `名称：`. If your matching
   uses `^名称`, **it silently matches nothing** and you conclude the drawing has no
   labels when it has dozens.
2. **Layer information can collapse to "0".** Conversion does not lose it; sloppy source
   drawings never had it. You cannot tell the difference from the output alone.

`audit.py` handles (1) in `plain_text()` and reports (2) as a finding.

---

## Recommended order

1. `dwg2dxf` everything - cheapest, catches most.
2. Run `audit.py` on the output folder.
3. Whatever `audit.py` marks `readable=no`, retry those *specific files* through ODA,
   then AutoCAD if needed.
4. Only then quote a BOM job - and quote the unreadable files as excluded, in writing.
