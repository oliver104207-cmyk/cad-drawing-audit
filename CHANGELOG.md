# Changelog

## 2026-11-16

### Added: `audit.py`

`audit.py` is now in this repo. **The README says it is not -- that line is stale.**
I could not edit the README through the web editor without risking the
reproduction section, so this file records the correction instead.

Verified by downloading it back from this repo and running it:

```
27 files -> 21 unique by MD5
audited 21 | readable 18 | failed 3 | issues 18
```

That matches `data/drawing_audit_21.csv` and the README reproduction block.
### Added: `STATUS.md`

States what works, what does not, and that no customer has paid. Written because
the repo is the only thing a stranger sees, and it should not look like a product
that has revenue when it has none.

### Added: reproduction snippet to README

A 20-line Python block that regenerates the headline counts from any DXF folder.
The point is that nobody should have to trust the numbers in this repo -- they can
recompute them.

### Known defect, unfixed

An 87 MB factory drawing (real, from a working plant) fails to parse. It has
20,696 instances of the `310` DXF group code -- binary chunks spliced into the
entity stream. Stripping them moves the failure from line 3,811,398 to line
1,382,464, where a second corruption (`Invalid tag 1071`) stops it.

**I did not solve this.** It is recorded here so it is not discovered by a
customer after they have paid.
