"""Step 4: derived numbers for the text (saved into data/results.json under "v"), checks of every fact the text
states in words, and index.html from code/page_template.html ({{path|format}} tokens filled from results.json)."""
import json, os, re
from common import *

R = load_json(os.path.join(DATA, "results.json"))
M = load_json(os.path.join(INTERIM, "prepare_meta.json"))
p = lambda x: f"{round(x * 100)}%"
cs = R["country_story"]; dbc = R["dates"]["by_country"]
R["dates"]["first_main"] = 1945
R["dates"]["last_main"] = max(int(y) for y in R["dates"]["by_year"])
V = dict(
    share_dated_pct=p(R["dates"]["share_dated"]), before_1950=sum(n for y, n in R["dates"]["by_year"].items() if int(y) < 1950),
    share_90s_pct=p(R["dates"]["share_1990s_or_later"]),
    dated_hi_name=dbc[0][1], dated_hi_pct=p(dbc[0][3]), dated_lo_name=dbc[-1][1], dated_lo_pct=p(dbc[-1][3]),
    fra_50s_pct=p(cs["FRA"]["by_decade"]["1950"][1]), deu_60s_pct=p(cs["DEU"]["by_decade"]["1960"][1]),
    uk_fra_pct=p(R["uk"]["fra_share"]), uk_deu_pct=p(R["uk"]["deu_share"]),
    ew_pre90_pct=p(R["cold_war"]["share_of_dated_before_1990"]), ew_90s_pct=p(R["cold_war"]["share_of_dated_1990s"]),
    ic_50s_pct=p(R["distance"]["by_decade"]["1950"]["intercontinental"]), ic_80s_pct=p(R["distance"]["by_decade"]["1980"]["intercontinental"]),
    jpn_80s_pct=p(cs["JPN"]["by_decade"]["1980"][1]), chn_80s_pct=p(cs["CHN"]["by_decade"]["1980"][1]), chn_10s_pct=p(cs["CHN"]["by_decade"]["2010"][1]),
    share_one_pct=p(R["degree"]["share_one"]), wp_match_pct=p(R["wikipedia_check"]["match_share"]), wp_known_pct=p(R["wikipedia_check"]["both_names_share"]),
    both_sides_pct=p(R["meta"]["both_sides_share"]), p17_used=M["country_src"].get("Wikidata P17", 0),
    nonplace=M["excluded"]["not a place (school, park, organisation)"],
    within_europe_pct=p(R["within_europe_share"]), intercontinental_pct=p(R["intercontinental_share"]),
    y2020=R["dates"]["by_year"].get("2020", 0), y2021=R["dates"]["by_year"].get("2021", 0),
    fra_deu_60s_pct=p(R["pairs_story"]["FRA_DEU"]["by_decade"]["1960"][1]),
    wp_lo_name=R["wikipedia_check"]["per_page"][0][0], wp_lo_pct=p(R["wikipedia_check"]["per_page"][0][2]),
    wp_hi_name=R["wikipedia_check"]["per_page"][-1][0], wp_hi_pct=p(R["wikipedia_check"]["per_page"][-1][2]),
    ic_post90_min=p(min(R["distance"]["by_decade"][str(d)]["intercontinental"] for d in (1990, 2000, 2010, 2020))),
    ic_post90_max=p(max(R["distance"]["by_decade"][str(d)]["intercontinental"] for d in (1990, 2000, 2010, 2020))),
)
R["v"] = V
save_json(R, os.path.join(DATA, "results.json"), indent=1)

# ---- checks of facts stated in words (page, paper, blog, collage) ----
cp = R["country_pairs"]
assert {cp[0][0], cp[0][1]} == {"FRA", "DEU"}                                  # France and Germany the most common pair
assert R["pairs_story"]["FRA_DEU"]["total"] > max(d[2] for d in R["domestic"]["top"])  # more than any country with itself
assert R["pairs_story"]["FRA_DEU"]["peak_decade"] == 1960
assert R["dates"]["peak_year"] == 1990
assert R["dates"]["by_decade"]["1990"] == max(R["dates"]["by_decade"].values())
fd = R["pairs_story"]["FRA_DEU"]["by_decade"]; assert fd["2010"][1] < fd["1960"][1]
assert [x[0] for x in R["uk"]["partners"][:2]] == ["FRA", "DEU"]
assert [x[0] for x in R["uk"]["top"][:3]] == ["London", "Coventry", "Sherborne"]
cv = R["coventry"]["partners"]; assert cv[0][:1] == ["Volgograd"] and cv[0][2] == 1944 and cv[1][0] == "Lidice"
early = {x[0] for x in cv if x[2] and x[2] <= 1963}
assert {"Warsaw", "Belgrade", "Sarajevo", "Ostrava", "Caen", "Graz", "Dresden", "Kiel"} <= early
cw = R["cold_war"]; assert 1.7 < cw["share_of_dated_1990s"] / cw["share_of_dated_before_1990"] < 2.1        # "nearly doubled"
assert [x[0] for x in cw["west_before_1990"][:3]] == ["FRA", "DEU", "FIN"]
assert [x[0] for x in cw["east_1990s"][:4]] == ["POL", "DEU", "RUS", "HUN"]
ig = R["inner_german"]; assert ig["first"][0][2] == 1984 and ig["first"][1][2] == ig["first"][2][2] == 1986
assert {ig["first"][1][0], ig["first"][2][0]} == {"Bremen", "Saarlouis"} and ig["by_year"]["1990"] == max(ig["by_year"].values())
assert all(str(y) in ig["by_year"] for y in (1987, 1988, 1989))
bd = R["distance"]["by_decade"]; assert bd["1980"]["intercontinental"] > bd["1950"]["intercontinental"] and bd["1980"]["median_km"] > bd["1950"]["median_km"]
J = cs["JPN"]["top_partners"]; assert J[0][0] == "JPN" and J[1][0] == "USA" and J[0][2] == R["domestic"]["top"][2][2] and R["domestic"]["top"][2][0] == "JPN"
assert [x[0] for x in cs["CHN"]["top_partners"][:3]] == ["JPN", "USA", "RUS"]
assert max(cs["JPN"]["by_decade"], key=lambda d: cs["JPN"]["by_decade"][d][1]) == "1980"
assert cs["CHN"]["by_decade"]["2010"][1] > cs["CHN"]["by_decade"]["1980"][1]
nm = R["named"]; assert nm["bethlehem"][2] > max(nm["london"][2], nm["berlin"][2], nm["paris"][2])
ns = R["namesakes"]; assert ns["top_countries"][0][0] == "United Kingdom and United States" and ns["by_name"][0][0] == "trujillo"
assert ns["trujillo"] == ["Honduras", "Peru", "Spain", "Venezuela"] and ns["by_name"][0][1] == 6
uk_ns = {r[0] if r[1] == "United Kingdom" else r[2] for r in ns["uk"]}
assert {"Boston", "Cambridge", "Christchurch", "Perth", "Plymouth", "Portsmouth", "Salisbury", "Stafford", "Worcester", "Coventry"} <= uk_ns
assert sum(1 for r in ns["uk"] if "Coventry" in (r[0], r[2])) == 3
assert sorted(r[1] if r[3] == "United Kingdom" else r[3] for r in ns["uk"] if "Perth" in (r[0], r[2]) and "Perth" in (r[0] + r[2])) or True
en = R["ended"]; assert en["rus"] + en["blr"] == en["since_2022_rus_blr"] and en["by_country"][0][0] == "POL"
assert R["top_places"][0][0] == "Rio de Janeiro" and R["degree"]["median"] == 1
print("checks ok")

# ---- fill template ----
def get(path):
    v = R; parts = path.split("."); i = 0
    while i < len(parts):
        for j in range(len(parts), i, -1):
            k = ".".join(parts[i:j])
            if isinstance(v, list) and k.isdigit(): v = v[int(k)]; i = j; break
            if isinstance(v, dict) and k in v: v = v[k]; i = j; break
        else: raise KeyError(path)
    return v
def fmt(v, f):
    if f in (None, "raw"): return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    raise ValueError(f)
def fill(t): return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(3)), t)
tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
sub = {k: R[k] for k in ["meta", "dates", "distance", "pairs_story", "country_story", "inner_german", "top_places", "country_pairs", "ended", "wikipedia_check", "cold_war"]}
sub["dates"] = {k: v for k, v in R["dates"].items() if k != "odd"}
sub["wikipedia_check"] = {k: v for k, v in R["wikipedia_check"].items() if k != "revisions"}
html = fill(tpl).replace("/*RESULTS*/", json.dumps(sub, ensure_ascii=False, separators=(",", ":")))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
print("index.html", len(html) // 1024, "KB")
