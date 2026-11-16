# Known failures

Every entry here is a real failure I hit, with the exact error text. Listed because
"it doesn't work" without the error message is useless.

---

## 1. MTEXT labels don't match ^名称

**Symptom:** drawing clearly has part-name labels when opened in AutoCAD, but your parser
reports 0 matches for `名称`.

**Error:** none. It returns an empty list and exits 0.

**Root cause:** MTEXT content is stored with inline formatting codes:

```
{\fSimSun|b0|i0|c134|p2;\H0.83333x;名称：}
```

`re.match(r'^名称', text)` fails because the string starts with `{`.

**Fix:** strip formatting before matching:

```python
s = re.sub(r"\\[A-Za-z][^;\\]*;", "", raw)   # \H0.83333x;  \fSimSun|...;
s = s.replace("{", "").replace("}", "").strip()
```

**Why this one matters:** it is a *silent* failure. It makes a drawing look like it has
no labels, so you report "no BOM possible" on a file that is actually fine. That is the
mirror image of the stacked-label bug below, and both produce confidently wrong output.

---

## 2. Stacked labels collapse three parts into one

**Symptom:** BOM has fewer rows than the drawing has parts. No error.

**Real data** (from `data/drawing_audit_21.csv`):

```
'名称： '   x=  55.0  y= 932.4
'名称： '   x=  55.0  y= 932.4
'名称： '   x=  55.0  y= 932.4
```

Three distinct parts share one label anchor point. Any "text nearest to geometry"
pairing returns the same name for all three.

**Fix:** detect duplicate anchor coordinates and refuse to auto-pair. Report the
collision and the pairing offset instead of guessing. `audit.py` flags this as
`「名称」标注坐标重合 N 处`.

**Do not** "solve" this by picking the first match. That is how you ship a BOM missing
two parts.

---

## 3. Invalid handle 0.

**File:** one of 21. Fails on `ezdxf.readfile` after successful conversion.

**Cause:** broken object handle references in the source DWG. Not recoverable at the DXF
stage.

**Action:** exclude from the batch, tell the customer which file and why. Do not silently
drop it - a missing file reads as "everything else is fine".

---

## 4. Invalid binary data near line: 3811398.

**Files:** two, both over 80 MB.

**Cause:** libredwg cannot walk that section at that size.

**Fallback:** ODA File Converter, or split the drawing. Still unsolved for >80 MB in this
toolchain - recorded as a known gap, not worked around.

---

## 5. AutoCAD COM: cannot get Document object

```
com_error(-2147352567, '发生意外。',
  (0, 'AutoCAD', '无法获取 Document 对象', ...))
```

**Cause:** `GetActiveObject("AutoCAD.Application")` succeeds but `Document` retrieval
fails. Usually: AutoCAD is running under a different login session than the script, or
it is starting up and has no document yet.

**Action:** do not build a pipeline that depends on this. It needs a desktop session, so
it cannot run unattended.

---

## 6. Two conversions of the same drawing hash differently

**Symptom:** dedup by MD5 reports 21 unique files from 27 - but you get pairs that
*look* identical (same size, same entity count) yet hash differently.

**Real case:**

```
EF3F552FC107   1,306,325  IMPORTED8_20261025_183928.dxf
A529F8289A0C   1,306,325  IMPORTED8_20261025_184006.dxf
A529F8289A0C   1,306,325  SOURCE8_READONLY_20261025_184124.dxf
```

Same source drawing, two conversion runs, byte-different output. MD5 dedup keeps 2 of
these 3. That is correct behaviour for MD5 and wrong behaviour for "how many unique
drawings do I have".

**Action:** when reporting counts to a customer, state the dedup method. "21 unique files
by MD5" is honest. "21 unique drawings" is a claim you have not proven.
