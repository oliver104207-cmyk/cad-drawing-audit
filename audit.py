#!/usr/bin/env python3
"""Audit DXF folders before trusting a BOM. See README for why each check matters.

python audit.py <dxf_folder> [-o out.xlsx]     needs: ezdxf openpyxl
"""
import argparse, collections, glob, hashlib, os, re, sys

try:
    import ezdxf
    from openpyxl import Workbook
except ImportError as e:
    sys.exit("%s -- pip install ezdxf openpyxl" % e)

PARTS = ["名称", "数量", "规格", "型号", "材料", "材质", "重量"]
PLANS = ["区", "室", "楼梯", "门", "走廊", "房间", "车间"]


def plain(raw):
    """MTEXT stores '{\\fSimSun|b0|..;\\H0.83x;名称：}'. ^名称 matches nothing."""
    if not raw:
        return ""
    return re.sub(r"\\[A-Za-z][^;\\]*;", "", raw).replace("{", "").replace("}", "").strip()

def one(path):
    r = {"file": os.path.basename(path), "ok": False, "ents": 0, "texts": 0,
         "layers": 0, "blocks": 0, "type": "未知", "issues": []}
    try:
        doc = ezdxf.readfile(path)
        msp = list(doc.modelspace())
        r.update(ents=len(msp), ok=True, layers=len(doc.layers))

        rows = []
        for e in msp:
            if e.dxftype() in ("TEXT", "MTEXT"):
                try:
                    t = e.dxf.text if e.dxftype() == "TEXT" else e.text
                    p = e.dxf.insert
                    rows.append((plain(t), float(p[0]), float(p[1])))
                except Exception:
                    pass
        r["texts"] = len(rows)

        anon = set()
        for e in msp:
            if e.dxftype() == "INSERT":
                try:
                    if e.dxf.name.startswith("*"):
                        anon.add(e.dxf.name)
                except Exception:
                    pass
        r["blocks"] = len(anon)
        tot = len(msp) or 1
        zero = sum(1 for e in msp if getattr(e.dxf, "layer", "0") == "0") / tot * 100

        anchors = collections.Counter(
            (round(x, 1), round(y, 1)) for t, x, y in rows if re.match(r"^名称[:：]", t))
        stacked = sum(1 for v in anchors.values() if v > 1)

        joined = " ".join(t for t, _, _ in rows)
        if any(k in joined for k in PARTS):
            r["type"] = "零件/BOM图"
        elif any(k in joined for k in PLANS):
            r["type"] = "平面布置图"
        elif not rows:
            r["type"] = "无文字（无法判断）"

        if zero > 90:
            r["issues"].append('图层未分类（%.0f%% 图元在 "0" 层）' % zero)
        if anon:
            r["issues"].append("匿名块 %d 个" % len(anon))
        if stacked:
            r["issues"].append("「名称」标注坐标重合 %d 处" % stacked)
        if not rows:
            r["issues"].append("无任何文字标注")
        if r["type"] == "零件/BOM图" and "数量" not in joined:
            r["issues"].append("零件图缺「数量」字段")
    except Exception as e:
        r["issues"].append("读取失败：" + str(e)[:70])
    return r

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("-o", "--out", default="drawing_audit.xlsx")
    a = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(a.folder, "*.dxf")))
    if not paths:
        sys.exit("no .dxf in %s" % a.folder)

    seen, uniq = set(), []
    for p in paths:
        h = hashlib.md5(open(p, "rb").read()).hexdigest()
        if h not in seen:
            seen.add(h)
            uniq.append(p)
    print("%d files -> %d unique by MD5" % (len(paths), len(uniq)))

    res = [one(p) for p in uniq]
    n = len(res)
    ok = sum(1 for r in res if r["ok"])
    ty = collections.Counter(r["type"] for r in res)
    # read failures have no text because we cannot open them - not "no text"
    notext = sum(1 for r in res if r["ok"] and not r["texts"])
    uncls = sum(1 for r in res if r["ok"] and r["type"] not in ("零件/BOM图", "平面布置图") and r["texts"])
    wb = Workbook()
    ws = wb.active
    ws.title = "Overview"
    for row in [("Drawings audited", n, ""), ("Readable", ok, "%.0f%%" % (ok / n * 100)),
                ("Failed to read", n - ok, "corrupt or version too new"),
                ("Part / BOM drawings", ty.get("零件/BOM图", 0), "can produce a BOM"),
                ("Floor plan drawings", ty.get("平面布置图", 0), "no BOM possible"),
                ("Zero text entities", notext, "opens fine, nothing to extract"),
                ("Unclassified", uncls, "has text, type unclear"),
                ("With issues", sum(1 for r in res if r["issues"]), "")]:
        ws.append(list(row))

    w2 = wb.create_sheet("Per drawing")
    w2.append(["#", "file", "readable", "entities", "text", "layers", "blocks", "type", "issues"])
    for i, r in enumerate(res, 1):
        w2.append([i, r["file"][:46], "yes" if r["ok"] else "no", r["ents"], r["texts"],
                   r["layers"], r["blocks"], r["type"], "; ".join(r["issues"])[:90]])

    w3 = wb.create_sheet("Issues")
    w3.append(["#", "issue", "drawings", "share"])
    c = collections.Counter()
    for r in res:
        for i in r["issues"]:
            c[re.sub(r"\d+", "N", i.split("（")[0].split("：")[0])] += 1
    for i, (k, v) in enumerate(c.most_common(), 1):
        w3.append([i, k, v, "%.0f%%" % (v / n * 100)])

    wb.save(a.out)
    print("saved:", a.out)
    print("audited %d | readable %d | failed %d | issues %d"
          % (n, ok, n - ok, sum(1 for r in res if r["issues"])))


if __name__ == "__main__":
    main()
