"""Step 1: read the two browser bundles (Wikidata via QLever, English Wikipedia list pages) and write tidy tables.

data/places.csv  every twinned place kept, with coordinates, country (by point in polygon on Natural Earth), continent
data/pairs.csv   every twinning as an undirected pair, with start and end years and distance
data/interim/    excluded items, Wikipedia list wikitext summary (for the coverage check in step 2)
"""
import gzip, json, os, re, collections, csv
import numpy as np
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from common import *

B = json.load(gzip.open(BUNDLE))
RG = json.load(gzip.open(REGIONS))
WD = B["wd"]
E = "<http://www.wikidata.org/entity/"


def tsv(name):
    lines = WD[name].split("\n")
    return [l.split("\t") for l in lines[1:] if l.strip()]


def qid(s):
    return s.replace(E, "").replace(">", "") if s else ""


def lit(s):
    if not s:
        return ""
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^.*)?$', s)
    v = m.group(1) if m else s
    v = v.replace('\\"', '"').replace("\\\\", "\\")
    return v.replace("\u2013", "-").replace("\u2014", "-")   # house style: no en or em dashes, even in names


def year(s):
    m = re.match(r'^"?(-?\d{1,4})-', s or "")
    return int(m.group(1)) if m else None


cls = {qid(r[0]): lit(r[1]) for r in tsv("cls")}
fb = {qid(r[0]): lit(r[1]) for r in tsv("fb")}
ctry = {qid(r[0]): (lit(r[1]), lit(r[2])) for r in tsv("ctry")}
reg = {}
rlab = {qid(r[0]): lit(r[1]) for r in [l.split("\t") for l in RG["labels"].split("\n")[1:] if l.strip()]}
for l in RG["reg"].split("\n")[1:]:
    if l.strip():
        x, st = l.split("\t")
        reg.setdefault(qid(x), set()).add(rlab.get(qid(st), qid(st)))

# ---- Natural Earth countries for point in polygon ----
ne = load_json(os.path.join(NE, "ne_50m_admin_0_countries.geojson"))
geoms, props = [], []
for f in ne["features"]:
    p = f["properties"]
    iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] not in ("-99", None) else p["ADM0_A3"]
    if p["ADM0_A3"] in ("KOS", "TWN", "CYN", "SOL", "SAH", "PSX"):
        iso = {"KOS": "XKX", "TWN": "TWN", "CYN": "CYN", "SOL": "SOL", "SAH": "ESH", "PSX": "PSE"}[p["ADM0_A3"]]
    geoms.append(shape(f["geometry"]))
    props.append((iso, p["NAME"], p["CONTINENT"]))
tree = STRtree(geoms)
ISO_INFO = {}
for iso, name, cont in props:
    ISO_INFO.setdefault(iso, (name, cont))


def locate(lat, lon):
    pt = Point(lon, lat)
    for i in tree.query(pt):
        if geoms[i].contains(pt):
            return props[i][0]
    i = tree.nearest(pt)
    if geoms[i].distance(pt) < 0.5:          # about 50 km: coastal and island points just outside the 1:50m outline
        return props[i][0]
    return None


NONPLACE = re.compile(r"school|lyc[eé]e|lyceum|gymnasium|hospital|church building|company|educational institution|"
                      r"urban park|natural park|national park|geopark|nonprofit|voluntary association|intergovernmental|"
                      r"AEFE|Baccalaureate", re.I)
COUNTRYCLS = re.compile(r"^(country|sovereign state|state with limited recognition)$", re.I)

nodes, excluded = {}, collections.Counter()
for r in tsv("nodes"):
    x = qid(r[0]); name = lit(r[1]) or fb.get(x, "") or x
    c = cls.get(qid(r[5]), "")
    m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", r[2] or "")
    if not m:
        excluded["no coordinates"] += 1; continue
    lon, lat = float(m.group(1)), float(m.group(2))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        excluded["bad coordinates"] += 1; continue
    if x == qid(r[3]) or COUNTRYCLS.match(c):
        excluded["a whole country"] += 1; continue
    if NONPLACE.search(c):
        excluded["not a place (school, park, organisation)"] += 1; continue
    iso = locate(lat, lon)
    src = "point in polygon"
    if iso is None:
        iso = ctry.get(qid(r[3]), ("", ""))[1] or ""
        src = "Wikidata P17"
    if not iso:
        excluded["no country"] += 1; continue
    pop = float(r[4]) if r[4] else None
    rg = reg.get(x, set())
    nodes[x] = dict(qid=x, name=name, lat=round(lat, 5), lon=round(lon, 5), iso3=iso, cls=c,
                    pop=int(pop) if pop and pop > 0 else None, region="|".join(sorted(rg)), country_src=src)

# ---- pairs ----
ends = collections.defaultdict(set)
for r in tsv("ends"):
    if r[3] if len(r) > 3 else "":
        ends[(qid(r[0]), qid(r[1]))].add(qid(r[3]))
P = {}
stmt_total = 0
for r in tsv("pairs"):
    stmt_total += 1
    a, b = qid(r[0]), qid(r[1])
    if a == b:
        continue
    k = tuple(sorted((a, b)))
    d = P.setdefault(k, dict(starts=set(), ends=set(), dirs=set(), causes=set()))
    d["dirs"].add((a, b))
    if year(r[2]) is not None: d["starts"].add(year(r[2]))
    if len(r) > 3 and year(r[3]) is not None: d["ends"].add(year(r[3]))
    d["causes"] |= ends.get((a, b), set())

rows, drop_pairs = [], collections.Counter()
deg = collections.Counter()
for (a, b), d in P.items():
    if a not in nodes or b not in nodes:
        drop_pairs["partner excluded or missing"] += 1; continue
    A, Bn = nodes[a], nodes[b]
    st = sorted(d["starts"])
    rows.append(dict(qid_a=a, qid_b=b, name_a=A["name"], name_b=Bn["name"], iso_a=A["iso3"], iso_b=Bn["iso3"],
                     start_year=st[0] if st else "", start_years_differ=int(len(st) > 1),
                     end_year=min(d["ends"]) if d["ends"] else "", end_cause="|".join(sorted(d["causes"])),
                     both_sides=int(len(d["dirs"]) == 2),
                     distance_km=round(haversine(A["lat"], A["lon"], Bn["lat"], Bn["lon"]), 1)))
    deg[a] += 1; deg[b] += 1

for x, n in nodes.items():
    n["degree"] = deg[x]
    n["country"], n["continent"] = ISO_INFO.get(n["iso3"], (ctry.get(n["iso3"], ("", ""))[0], ""))
keep = [n for n in nodes.values() if n["degree"] > 0]
# continent for codes that only came from Wikidata P17
for n in keep:
    if not n["continent"]:
        n["continent"] = "Unknown"

with open(os.path.join(DATA, "places.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["qid", "name", "lat", "lon", "iso3", "country", "continent", "region", "pop", "cls", "degree", "country_src"])
    w.writeheader()
    for n in sorted(keep, key=lambda n: (-n["degree"], n["name"])):
        w.writerow({k: n.get(k) for k in w.fieldnames})
with open(os.path.join(DATA, "pairs.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in sorted(rows, key=lambda r: (r["name_a"], r["name_b"])):
        w.writerow(r)

# ---- Wikipedia list pages: count partner bullet lines per page, and parse host/partner link targets ----
wp = B["wp"]
wsum = []
wpairs = []
for title, p in sorted(wp.items()):
    t = re.sub(r"<!--.*?-->", "", p["text"], flags=re.S)
    host = None; n = 0
    for line in t.split("\n"):
        m = re.match(r"^'''\s*\[\[([^\]|]+)(\|[^\]]*)?\]\]", line.strip())
        if m:
            host = m.group(1).strip(); continue
        if line.startswith("*") and host:
            m2 = re.search(r"\{\{flag(?:deco|icon)\|([^}|]+)[^}]*\}\}\s*\[\[([^\]|]+)", line)
            if m2:
                n += 1
                wpairs.append((title.replace("List of twin towns and sister cities in ", ""), host, m2.group(2).strip(), m2.group(1).strip()))
    wsum.append(dict(page=title, revid=p["revid"], timestamp=p["ts"], partner_lines=n))
with gzip.open(os.path.join(INTERIM, "wikipedia_lists.json.gz"), "wt", encoding="utf-8") as f:
    json.dump(dict(pages=wsum, pairs=wpairs), f, ensure_ascii=False)

meta = dict(retrieved=B["retrieved"][:10], statements=stmt_total, items=len(tsv("nodes")), excluded=dict(excluded),
            pairs_dropped=dict(drop_pairs), places=len(keep), pairs=len(rows), wp_pages=len(wp), wp_pairs=len(wpairs),
            country_src=dict(collections.Counter(n["country_src"] for n in keep)))
save_json(meta, os.path.join(INTERIM, "prepare_meta.json"), indent=1)
print(json.dumps(meta, indent=1))
