"""Step 2: every number for the page, paper, blog and collage, saved to data/results.json."""
import os, re, json, collections, unicodedata
import numpy as np
import pandas as pd
from common import *

P = pd.read_csv(os.path.join(DATA, "pairs.csv"))
N = pd.read_csv(os.path.join(DATA, "places.csv"))
M = load_json(os.path.join(INTERIM, "prepare_meta.json"))
NI = N.set_index("qid")
R = {}

# ---- short country names ----
SHORT = {"United States of America": "United States", "United Kingdom": "United Kingdom", "Czechia": "Czechia",
         "Bosnia and Herz.": "Bosnia and Herzegovina", "Dominican Rep.": "Dominican Republic", "Central African Rep.": "Central African Republic",
         "Dem. Rep. Congo": "DR Congo", "Congo": "Congo", "Eq. Guinea": "Equatorial Guinea", "S. Sudan": "South Sudan",
         "Solomon Is.": "Solomon Islands", "Marshall Is.": "Marshall Islands", "N. Cyprus": "Northern Cyprus", "W. Sahara": "Western Sahara",
         "Fr. Polynesia": "French Polynesia", "Faeroe Is.": "Faroe Islands", "Cayman Is.": "Cayman Islands", "Falkland Is.": "Falkland Islands",
         "St. Kitts and Nevis": "St Kitts and Nevis", "St. Vin. and Gren.": "St Vincent", "Antigua and Barb.": "Antigua and Barbuda",
         "São Tomé and Principe": "São Tomé and Príncipe", "Micronesia": "Micronesia", "Côte d'Ivoire": "Côte d'Ivoire",
         "Macedonia": "North Macedonia", "eSwatini": "Eswatini", "Turks and Caicos Is.": "Turks and Caicos", "British Virgin Is.": "British Virgin Islands",
         "U.S. Virgin Is.": "US Virgin Islands", "N. Mariana Is.": "Northern Mariana Islands", "Fr. S. Antarctic Lands": "French Southern Lands",
         "Wallis and Futuna Is.": "Wallis and Futuna", "St. Pierre and Miquelon": "St Pierre and Miquelon", "Åland": "Åland",
         "Heard I. and McDonald Is.": "Heard Island", "Pitcairn Is.": "Pitcairn", "Cook Is.": "Cook Islands", "Saint Helena": "St Helena",
         "Br. Indian Ocean Ter.": "British Indian Ocean Territory", "Indian Ocean Ter.": "Australian Indian Ocean Territories",
         "S. Geo. and the Is.": "South Georgia", "Siachen Glacier": "Siachen Glacier", "Saint Lucia": "St Lucia"}
CN = {}
for iso, c in zip(N.iso3, N.country):
    CN[iso] = SHORT.get(c, c)
# continents: Natural Earth CONTINENT, small-island ocean entries folded into Africa (Indian Ocean)
N.loc[N.continent.str.startswith("Seven"), "continent"] = "Africa"
CONT = dict(zip(N.iso3, N.continent))
NI = N.set_index("qid")
P["cont_a"] = P.iso_a.map(CONT); P["cont_b"] = P.iso_b.map(CONT)

R["meta"] = dict(retrieved=M["retrieved"], statements=M["statements"], items=M["items"], places=len(N), pairs=len(P),
                 excluded=M["excluded"], pairs_dropped=sum(M["pairs_dropped"].values()), countries=int(N.iso3.nunique()),
                 both_sides=int(P.both_sides.sum()), both_sides_share=round(float(P.both_sides.mean()), 4),
                 start_years_differ=int(P.start_years_differ.sum()))

# ---- dates ----
dated = P[P.start_year.notna()].copy()
odd = dated[(dated.start_year < 1900) | (dated.start_year > 2026)]
dated = dated[(dated.start_year >= 1900) & (dated.start_year <= 2026)]
dated["dec"] = (dated.start_year // 10 * 10).astype(int)
R["dates"] = dict(n_dated=int(len(dated)), share_dated=round(len(dated) / len(P), 4), n_odd=int(len(odd)),
                  odd=[[a, b, int(y)] for a, b, y in zip(odd.name_a, odd.name_b, odd.start_year)],
                  median_year=int(dated.start_year.median()), first_year=int(dated.start_year.min()),
                  by_year={int(y): int(n) for y, n in dated.start_year.value_counts().sort_index().items()},
                  by_decade={int(d): int(n) for d, n in dated.dec.value_counts().sort_index().items()},
                  peak_year=int(dated.start_year.value_counts().idxmax()), peak_year_n=int(dated.start_year.value_counts().max()),
                  share_1990s_or_later=round(float((dated.start_year >= 1990).mean()), 4),
                  share_before_1970=round(float((dated.start_year < 1970).mean()), 4))
early = dated.sort_values("start_year").head(8)
R["dates"]["earliest"] = [[a, CN[ia], b, CN[ib], int(y)] for a, ia, b, ib, y in zip(early.name_a, early.iso_a, early.name_b, early.iso_b, early.start_year)]
# share dated by country (coverage of dates)
rows = []
for iso, g in pd.concat([P.assign(iso=P.iso_a), P[P.iso_a != P.iso_b].assign(iso=P.iso_b)]).groupby("iso"):
    if len(g) >= 150:
        rows.append([iso, CN[iso], int(len(g)), round(float(g.start_year.notna().mean()), 3)])
rows.sort(key=lambda r: -r[3])
R["dates"]["by_country"] = rows

# ---- places and countries ----
top = N.sort_values(["degree", "pop"], ascending=[False, False]).head(30)
R["top_places"] = [[n, CN[i], int(d)] for n, i, d in zip(top.name, top.iso3, top.degree)]
R["degree"] = dict(mean=round(float(N.degree.mean()), 2), median=int(N.degree.median()),
                   one=int((N.degree == 1).sum()), share_one=round(float((N.degree == 1).mean()), 3),
                   ten_plus=int((N.degree >= 10).sum()), twenty_plus=int((N.degree >= 20).sum()))
cp = collections.Counter(); cpairs = collections.Counter(); dom = collections.Counter()
for a, b in zip(P.iso_a, P.iso_b):
    cpairs[tuple(sorted((a, b)))] += 1
    cp[a] += 1
    if a != b: cp[b] += 1
    else: dom[a] += 1
R["countries"] = [[i, CN[i], int(n), int(dom[i]), int((N.iso3 == i).sum())] for i, n in cp.most_common()]
R["country_pairs"] = [[a, b, CN[a], CN[b], int(n)] for (a, b), n in cpairs.most_common(40)]
R["domestic"] = dict(n=int(sum(dom.values())), share=round(sum(dom.values()) / len(P), 4),
                     top=[[i, CN[i], int(n)] for i, n in dom.most_common(8)])
R["n_country_pairs"] = len(cpairs)
# continents
cc = collections.Counter(tuple(sorted((a, b))) for a, b in zip(P.cont_a, P.cont_b))
R["continent_pairs"] = [[a, b, int(n)] for (a, b), n in cc.most_common()]
R["within_europe_share"] = round(cc[("Europe", "Europe")] / len(P), 4)
R["intercontinental_share"] = round(float((P.cont_a != P.cont_b).mean()), 4)

# ---- distance ----
R["distance"] = dict(median_km=int(P.distance_km.median()), under_1000_share=round(float((P.distance_km < 1000).mean()), 3),
                     over_5000_share=round(float((P.distance_km > 5000).mean()), 3))
byd = {}
for d, g in dated.groupby("dec"):
    if d >= 1940:
        byd[int(d)] = dict(n=int(len(g)), median_km=int(g.distance_km.median()),
                           intercontinental=round(float((g.cont_a != g.cont_b).mean()), 3),
                           europe_only=round(float(((g.cont_a == "Europe") & (g.cont_b == "Europe")).mean()), 3))
R["distance"]["by_decade"] = byd
far = P.sort_values("distance_km", ascending=False).head(5)
R["distance"]["longest"] = [[a, CN[ia], b, CN[ib], int(d)] for a, ia, b, ib, d in zip(far.name_a, far.iso_a, far.name_b, far.iso_b, far.distance_km)]

# ---- decade shares for named country pairs and countries ----
def pair_mask(df, a, b):
    return ((df.iso_a == a) & (df.iso_b == b)) | ((df.iso_a == b) & (df.iso_b == a))
def inv_mask(df, a):
    return (df.iso_a == a) | (df.iso_b == a)
dec_tot = dated.dec.value_counts()
DECS = [d for d in range(1950, 2030, 10)]
def series(mask):
    s = dated[mask].dec.value_counts()
    return {d: [int(s.get(d, 0)), round(float(s.get(d, 0) / dec_tot.get(d, 1)), 4)] for d in DECS}
R["pairs_story"] = {}
for k, (a, b) in {"FRA_DEU": ("FRA", "DEU"), "FRA_GBR": ("FRA", "GBR"), "DEU_GBR": ("DEU", "GBR"), "DEU_POL": ("DEU", "POL"),
                  "JPN_USA": ("JPN", "USA"), "CHN_USA": ("CHN", "USA"), "CHN_JPN": ("CHN", "JPN"), "POL_UKR": ("POL", "UKR")}.items():
    m = pair_mask(P, a, b); md = pair_mask(dated, a, b)
    R["pairs_story"][k] = dict(total=int(m.sum()), dated=int(md.sum()), by_decade=series(md),
                               median_year=int(dated[md].start_year.median()) if md.sum() else None,
                               peak_decade=int(dated[md].dec.value_counts().idxmax()) if md.sum() else None)
R["country_story"] = {}
for c in ["CHN", "JPN", "USA", "KOR", "FRA", "DEU", "GBR", "RUS", "UKR", "POL", "TUR", "ITA"]:
    m = inv_mask(P, c); md = inv_mask(dated, c)
    part = collections.Counter(b if a == c else a for a, b in zip(P[m].iso_a, P[m].iso_b))
    R["country_story"][c] = dict(total=int(m.sum()), dated=int(md.sum()), share_dated=round(float(md.sum() / max(1, m.sum())), 3),
                                 by_decade=series(md), median_year=int(dated[md].start_year.median()),
                                 top_partners=[[i, CN[i], int(n)] for i, n in part.most_common(6)])
FD = R["pairs_story"]["FRA_DEU"]["by_decade"]
R["fra_deu_rank"] = [i for i, ((a, b), n) in enumerate(cpairs.most_common()) if {a, b} == {"FRA", "DEU"}][0] + 1

# ---- Cold War: Eastern bloc (Warsaw Pact members and Soviet republics by present-day country, plus the five eastern German
#      states) with NATO members as of 1989 (plus West German states) and western neutrals ----
EASTC = {"RUS", "UKR", "BLR", "MDA", "EST", "LVA", "LTU", "GEO", "ARM", "AZE", "KAZ", "UZB", "TKM", "KGZ", "TJK",
         "POL", "CZE", "SVK", "HUN", "ROU", "BGR"}
NATO89 = {"USA", "CAN", "GBR", "FRA", "BEL", "NLD", "LUX", "NOR", "DNK", "ISL", "ITA", "PRT", "GRC", "TUR", "ESP"}
NEUTRAL = {"AUT", "CHE", "SWE", "FIN", "IRL"}
EASTDE = {"Brandenburg", "Mecklenburg-Vorpommern", "Saxony", "Saxony-Anhalt", "Thuringia"}
def side(q, iso):
    if iso == "DEU":
        r = NI.region.get(q)
        s = set(r.split("|")) if isinstance(r, str) else set()
        if s & EASTDE: return "E"
        if "Berlin" in s or not s: return None
        return "W"
    if iso in EASTC: return "E"
    if iso in NATO89 or iso in NEUTRAL: return "W"
    return None
P["side_a"] = [side(q, i) for q, i in zip(P.qid_a, P.iso_a)]
P["side_b"] = [side(q, i) for q, i in zip(P.qid_b, P.iso_b)]
P["ew"] = [(isinstance(a, str) and isinstance(b, str) and a != b) for a, b in zip(P.side_a, P.side_b)]
dated = dated.join(P[["ew", "side_a", "side_b"]])
ewd = dated[dated.ew]
R["cold_war"] = dict(ew_total=int(P.ew.sum()), ew_dated=int(len(ewd)),
                     ew_before_1990=int((ewd.start_year < 1990).sum()), ew_1990_on=int((ewd.start_year >= 1990).sum()),
                     ew_1990_1999=int(((ewd.start_year >= 1990) & (ewd.start_year < 2000)).sum()),
                     by_decade=series(dated.ew),
                     share_of_dated_before_1990=round(float(dated[dated.start_year < 1990].ew.mean()), 4),
                     share_of_dated_1990s=round(float(dated[(dated.start_year >= 1990) & (dated.start_year < 2000)].ew.mean()), 4))
# which western countries carried the Cold War links before 1990
pre = ewd[ewd.start_year < 1990]
wc = collections.Counter((a if sa == "W" else b) for a, b, sa in zip(pre.iso_a, pre.iso_b, pre.side_a))
ec = collections.Counter((a if sa == "E" else b) for a, b, sa in zip(pre.iso_a, pre.iso_b, pre.side_a))
R["cold_war"]["west_before_1990"] = [[i, CN[i], int(n)] for i, n in wc.most_common(6)]
R["cold_war"]["east_before_1990"] = [[i, CN[i], int(n)] for i, n in ec.most_common(6)]
# inner-German pairs
de = P[(P.iso_a == "DEU") & (P.iso_b == "DEU")]
ide = de[[{a, b} == {"E", "W"} for a, b in zip(de.side_a, de.side_b)]]
ided = ide[ide.start_year.notna()]
R["inner_german"] = dict(n=int(len(ide)), dated=int(len(ided)), before_1990=int((ided.start_year < 1990).sum()),
                         in_1990=int((ided.start_year == 1990).sum()), y1989=int((ided.start_year == 1989).sum()),
                         first=[[a, b, int(y)] for a, b, y in ided.sort_values("start_year").head(4)[["name_a", "name_b", "start_year"]].values],
                         by_year={int(y): int(n) for y, n in ided.start_year.value_counts().sort_index().items()},
                         share_of_domestic_de=round(len(ide) / max(1, len(de)), 3), domestic_de=int(len(de)))

# ---- namesakes: same name, different countries ----
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = s.split(",")[0]
    s = re.sub(r"\b(municipality|city of|city|borough of|district|town|urban district|county|metropolitan borough of|gmina|stadt|ville de)\b", "", s)
    s = re.sub(r"^(saint|st\.?|sankt|san|santa|sao)\s", "st ", s)
    return re.sub(r"[^a-z]+", "", s)
P["na"] = P.name_a.map(norm); P["nb"] = P.name_b.map(norm)
ns = P[(P.na == P.nb) & (P.na.str.len() >= 3) & (P.iso_a != P.iso_b)]
R["namesakes"] = dict(n=int(len(ns)), share=round(len(ns) / len(P), 4),
                      by_name=[[k, int(v)] for k, v in collections.Counter(ns.na).most_common(12)],
                      uk=[[a, CN[ia], b, CN[ib], int(y) if y == y else None] for a, ia, b, ib, y in
                          ns[(ns.iso_a == "GBR") | (ns.iso_b == "GBR")].sort_values("name_a")[["name_a", "iso_a", "name_b", "iso_b", "start_year"]].values],
                      top_countries=[[f"{CN[a]} and {CN[b]}", int(n)] for (a, b), n in collections.Counter(tuple(sorted((a, b))) for a, b in zip(ns.iso_a, ns.iso_b)).most_common(6)])
nsn = collections.Counter(ns.na)
P["namesake"] = P.index.isin(ns.index)

# ---- ended twinnings (P582 end time) ----
en = P[P.end_year.notna()].copy()
en["rus"] = en.iso_a.isin(["RUS", "BLR"]) | en.iso_b.isin(["RUS", "BLR"])
late = en[en.end_year >= 2022]
lr = late[late.rus]
other = collections.Counter((b if a in ("RUS", "BLR") else a) for a, b in zip(lr.iso_a, lr.iso_b))
rb = collections.Counter((a if a in ("RUS", "BLR") else b) for a, b in zip(lr.iso_a, lr.iso_b))
rus_total = int(inv_mask(P, "RUS").sum() + inv_mask(P, "BLR").sum())
R["ended"] = dict(n=int(len(en)), since_2022=int(len(late)), since_2022_rus_blr=int(len(lr)),
                  rus_blr_share_of_2022=round(len(lr) / max(1, len(late)), 3),
                  rus=int(rb.get("RUS", 0)), blr=int(rb.get("BLR", 0)),
                  by_country=[[i, CN[i], int(n)] for i, n in other.most_common(10)],
                  by_year={int(y): int(n) for y, n in lr.end_year.value_counts().sort_index().items()},
                  rus_blr_pairs_total=rus_total,
                  rus_still_open=int((inv_mask(P, "RUS") & P.end_year.isna()).sum()),
                  examples=[[a, CN[ia], b, CN[ib], int(y)] for a, ia, b, ib, y in lr.sort_values(["end_year", "name_a"]).head(12)[["name_a", "iso_a", "name_b", "iso_b", "end_year"]].values])

# ---- UK ----
uk = P[inv_mask(P, "GBR")]
ukp = N[N.iso3 == "GBR"]
part = collections.Counter(b if a == "GBR" else a for a, b in zip(uk.iso_a, uk.iso_b))
nation = collections.Counter()
for q, r in zip(ukp.qid, ukp.region):
    nation[r if isinstance(r, str) and r in ("England", "Scotland", "Wales", "Northern Ireland") else "unknown"] += 1
tu = ukp.sort_values(["degree", "pop"], ascending=False).head(10)
R["uk"] = dict(pairs=int(len(uk)), places=int(len(ukp)), dated=int(uk.start_year.notna().sum()),
               partners=[[i, CN[i], int(n)] for i, n in part.most_common(8)],
               fra_share=round(part["FRA"] / len(uk), 3), deu_share=round(part["DEU"] / len(uk), 3),
               top=[[n, int(d)] for n, d in zip(tu.name, tu.degree)], nations=dict(nation),
               median_year=int(uk.start_year.median()))

# ---- most-twinned ----
R["hubs"] = dict(n_over_50=int((N.degree > 50).sum()), top_capitals=None)

# ---- Wikipedia coverage check ----
import gzip
W = json.load(gzip.open(os.path.join(INTERIM, "wikipedia_lists.json.gz"), "rt", encoding="utf-8"))
wd_pairs = set()
names_by_norm = collections.defaultdict(set)
for a, b in zip(P.na, P.nb):
    wd_pairs.add((a, b)); wd_pairs.add((b, a))
wd_names = set(P.na) | set(P.nb)
hit = tot = known = 0
per_page = collections.defaultdict(lambda: [0, 0])
for page, host, partner, code in W["pairs"]:
    h, p = norm(host), norm(partner)
    if not h or not p: continue
    tot += 1; per_page[page][1] += 1
    if (h, p) in wd_pairs:
        hit += 1; per_page[page][0] += 1
    if h in wd_names and p in wd_names: known += 1
pp = sorted([[k, v[1], round(v[0] / v[1], 3)] for k, v in per_page.items() if v[1] >= 150], key=lambda r: r[2])
R["wikipedia_check"] = dict(pages=len(W["pages"]), lines=tot, matched=hit, match_share=round(hit / tot, 3),
                            both_names_known=known, both_names_share=round(known / tot, 3),
                            lowest=pp[:6], highest=pp[-6:], per_page=pp,
                            revisions={p["page"].replace("List of twin towns and sister cities in ", ""): p["revid"] for p in W["pages"]})


# ---- Coventry, a well-known early twinner, from the data ----
cv = P[(P.name_a == "Coventry") & (P.iso_a == "GBR") | (P.name_b == "Coventry") & (P.iso_b == "GBR")]
R["coventry"] = dict(n=int(len(cv)), partners=sorted([[b if (a == "Coventry" and ia == "GBR") else a, CN[ib if (a == "Coventry" and ia == "GBR") else ia], int(y) if y == y else None]
                     for a, ia, b, ib, y in cv[["name_a", "iso_a", "name_b", "iso_b", "start_year"]].values], key=lambda r: (r[2] or 9999, r[0])))
# ---- legend classes ----
def era(y):
    if not (y == y) or y < 1900 or y > 2026: return "No date"
    if y < 1960: return "Before 1960"
    if y >= 2010: return "2010 on"
    return f"{int(y)//10*10}s"
R["era_counts"] = dict(collections.Counter(era(y) for y in P.start_year))
def cpair(a, b):
    s = {a, b}
    if "Africa" in s: return "Africa"
    if "Oceania" in s: return "Oceania"
    am = {"North America", "South America"}
    if s == {"Europe"}: return "Within Europe"
    if s == {"Asia"}: return "Within Asia"
    if s <= am: return "Within the Americas"
    if "Europe" in s and "Asia" in s: return "Europe and Asia"
    if "Europe" in s: return "Europe and the Americas"
    return "Asia and the Americas"
R["cont_counts"] = dict(collections.Counter(cpair(a, b) for a, b in zip(P.cont_a, P.cont_b)))


# ---- a few named places for comparison in the text ----
def deg_of(name, iso):
    m = N[(N.name == name) & (N.iso3 == iso)]
    return [name, CN[iso], int(m.degree.max()), int(m["pop"].max()) if m["pop"].notna().any() else None]
R["named"] = {k: deg_of(*v) for k, v in {"bethlehem": ("Bethlehem", "PSE"), "london": ("London", "GBR"), "berlin": ("Berlin", "DEU"),
              "paris": ("Paris", "FRA"), "rome": ("Rome", "ITA"), "tokyo": ("Tokyo", "JPN")}.items()}
x = dated[dated.ew & (dated.start_year >= 1990) & (dated.start_year < 2000)]
R["cold_war"]["east_1990s"] = [[i, CN[i], int(n)] for i, n in collections.Counter((a if sa == "E" else b) for a, b, sa in zip(x.iso_a, x.iso_b, x.side_a)).most_common(6)]
tr = P[(P.na == "trujillo") & (P.nb == "trujillo")]
R["namesakes"]["trujillo"] = sorted(set(CN[i] for i in list(tr.iso_a) + list(tr.iso_b)))

save_json(R, os.path.join(DATA, "results.json"), indent=1)
# extra columns used by the page build
P[["ew", "namesake"]].astype(int).to_csv(os.path.join(INTERIM, "pair_flags.csv"), index=False)
for k in ["meta", "dates", "degree", "domestic", "distance", "cold_war", "inner_german", "namesakes", "ended", "uk", "wikipedia_check"]:
    v = {kk: vv for kk, vv in R[k].items() if kk not in ("by_year", "per_page", "revisions", "odd", "uk", "by_country")} if isinstance(R[k], dict) else R[k]
    print(k, json.dumps(v, ensure_ascii=False)[:900])
print(R["top_places"][:12]); print(R["country_pairs"][:12])
for k, v in R["pairs_story"].items(): print(k, v["total"], v["dated"], v["median_year"], {d: x[0] for d, x in v["by_decade"].items()})
for k, v in R["country_story"].items(): print(k, v["total"], v["share_dated"], v["median_year"], {d: x[1] for d, x in v["by_decade"].items()}, v["top_partners"][:3])
print(R["continent_pairs"][:10])
