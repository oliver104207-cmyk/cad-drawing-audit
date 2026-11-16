# Status

Last updated: 2026-11-16

## What works

| Thing | State |
|---|---|
| `audit.py` | **in this repo, verified** |
| `data/drawing_audit_21.csv` | 21 rows, one per unique file |
| README reproduction snippet | verified: 21 unique / 18 readable / 3 failed / 151048 entities |
## The one number you can check without trusting me

Download `audit.py` from this repo, point it at any folder of DXFs, run it.
On the same 27 source files it prints:

```
27 files -> 21 unique by MD5
audited 21 | readable 18 | failed 3 | issues 18
```

That was verified by downloading the file back from this repo and running it,
not by running the local copy. If you get different output, your folder is different.
## What this is not

- It does not fix drawings. It tells you which ones need a human before you quote.
- It does not read DWG directly. Convert first: `dwg2dxf --as r2018 -y in.dwg`
- It does not handle files with heavy binary chunks (the `310` group code).
  A 87 MB real drawing with 20,696 such chunks fails to parse. That is a known
  limit, not something I have solved.
## Known limits, stated plainly

1. **Large corrupted DXFs fail.** One 87 MB factory drawing had binary data spliced
   into the entity stream and would not parse. Stripping the `310` groups moved the
   failure point from line 3,811,398 to line 1,382,464 -- then it hit a second
   corruption (`Invalid tag 1071`) and stopped.
2. **Empty vs. lost.** If a DWG round-trips through libredwg and comes back with
   zero entities, I cannot tell whether the drawing was blank or the conversion ate it.
   The tool says so instead of guessing.
3. **No customer has paid for this.** Zero. That is the honest state.
