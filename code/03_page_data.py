"""Step 3: compact data for the interactive page.

data/page.json       places, pairs and country names for the map and the per-town panel
data/countries.json  Natural Earth 1:50m countries (simplified), copied from study-abroad (same file as games-on-the-map)
data/towns.json, data/hills.png  the generic world place-name and hill-shading layers used by games-on-the-map and
                     study-abroad (GeoNames cities15000, CC BY 4.0; AWS Terrain Tiles); copied, not recomputed
"""
import os, shutil
import pandas as pd
from common import *

SHARED = os.environ.get("TT_SHARED", "/home/claude/hist/study-abroad/data")
for f in ["countries.json", "towns.json", "hills.png"]:
    if not os.path.exists(os.path.join(DATA, f)):
        shutil.copy(os.path.join(SHARED, f), os.path.join(DATA, f))

R = load_json(os.path.join(DATA, "results.json"))
N = pd.read_csv(os.path.join(DATA, "places.csv"))
P = pd.read_csv(os.path.join(DATA, "pairs.csv"))
FL = pd.read_csv(os.path.join(INTERIM, "pair_flags.csv"))
CN = {r[0]: r[1] for r in R["countries"]}
N.loc[N.continent.str.startswith("Seven"), "continent"] = "Africa"
codes = sorted(set(N.iso3))
CI = {c: i for i, c in enumerate(codes)}
CONTS = ["Europe", "Asia", "North America", "South America", "Africa", "Oceania"]
cont = {}
for iso, c in zip(N.iso3, N.continent):
    cont[iso] = CONTS.index(c) if c in CONTS else 4
QI = {q: i for i, q in enumerate(N.qid)}
places = []
for q, n, la, lo, iso, pop, deg in zip(N.qid, N.name, N.lat, N.lon, N.iso3, N["pop"], N.degree):
    places.append([n, round(la, 4), round(lo, 4), CI[iso], int(deg), int(pop) if pop == pop else 0, q])
pairs = []
for a, b, s, e, bs, ew, ns in zip(P.qid_a, P.qid_b, P.start_year, P.end_year, P.both_sides, FL.ew, FL.namesake):
    s = int(s) if s == s and 1900 <= s <= 2026 else 0
    pairs += [QI[a], QI[b], s, int(e) if e == e else 0, int(bs) + 2 * int(ew) + 4 * int(ns)]
page = dict(codes=codes, names=[CN.get(c, c) for c in codes], cont=[cont[c] for c in codes], conts=CONTS, places=places, pairs=pairs)
save_json(page, os.path.join(DATA, "page.json"))
print("page.json", os.path.getsize(os.path.join(DATA, "page.json")) // 1024, "KB", len(places), len(pairs) // 5)
