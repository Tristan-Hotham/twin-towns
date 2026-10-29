"""Step 6: the paper PDF. Fills code/paper_template.tex from data/results.json, checks facts stated only in the paper,
writes release/paper/Hotham_Twin_Towns.tex and compiles it with xelatex (figures from step 5)."""
import os, re, shutil, subprocess, importlib
from common import *
site = importlib.import_module("04_build_site")
R = site.R
# facts stated only in the paper
cw = R["cold_war"]; assert [x[0] for x in cw["east_before_1990"][:3]] == ["DEU", "RUS", "POL"]
assert {x[0] for x in cw["east_1990s"][:10]} >= {"POL", "DEU", "RUS", "HUN"}
assert R["domestic"]["top"][0][0] == "DEU" and [x[0] for x in R["domestic"]["top"][:3]] == ["DEU", "ITA", "JPN"]
assert [tuple(sorted(x[:2])) for x in R["country_pairs"][:4]] == [("DEU", "FRA"), ("DEU", "DEU"), ("FRA", "ITA"), ("FRA", "GBR")]
ps = R["pairs_story"]["DEU_POL"]["by_decade"]; assert max(ps, key=lambda d: ps[d][0]) == "1990"
us = R["country_story"]["USA"]["by_decade"]; assert max(us, key=lambda d: us[d][1]) == "1980"
assert R["dates"]["by_year"]["2020"] < R["dates"]["by_year"]["2019"] and R["dates"]["by_year"]["2021"] < R["dates"]["by_year"]["2019"]
assert R["ended"]["by_country"][1][0] == "LTU" and R["ended"]["by_country"][2][0] == "FIN"
print("paper checks ok")

tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    return tex(v)
SN = {"United Kingdom": "United Kingdom", "United States": "United States"}
rows = "".join((f"Within {tex(r[2])}" if r[0] == r[1] else f"{tex(r[2])} and {tex(r[3])}") + f" & {r[4]:,}\\\\\n" for r in R["country_pairs"][:12])
TCP = ("\\begin{table}[tbp]\\centering\\small\\caption{The most common pairs of countries among the " + f"{R['meta']['pairs']:,}" + " twinnings.}\\label{tab:cp}"
       "\\begin{tabular}{lr}\\toprule Countries & Pairs\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
bd = R["distance"]["by_decade"]; ew = R["cold_war"]["by_decade"]
dr = ""
for d in [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]:
    b = bd[str(d)]
    dr += f"{d}s & {b['n']:,} & {b['median_km']:,} & {b['intercontinental'] * 100:.0f}\\% & {b['europe_only'] * 100:.0f}\\% & {ew[str(d)][1] * 100:.0f}\\%\\\\\n"
TDEC = ("\\begin{table}[tbp]\\centering\\small\\caption{Dated twinnings by decade of start: number, median distance between partners, "
        "share between continents, share within Europe, and share joining the two Cold War camps (present-day countries). The 2020s run to " + str(R["dates"]["last_main"]) + ".}\\label{tab:dec}"
        "\\begin{tabular}{lrrrrr}\\toprule Decade & Pairs & Median km & Between continents & Within Europe & East and West\\\\\\midrule\n" + dr + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{TABLE_CP}}", TCP).replace("{{TABLE_DEC}}", TDEC)
t = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(site.get(m.group(1)), m.group(3)), t)
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Twin_Towns"
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if r.returncode: print(r.stdout[-3000:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("pdf", os.path.getsize(os.path.join(ROOT, "release", NAME + ".pdf")) // 1024, "KB")
