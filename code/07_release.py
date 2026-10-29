"""Step 7: blog post (release/blog/post.html, meta.json), Zenodo files (release/zenodo/), README.md and LICENSE."""
import os, re, json, shutil, zipfile, importlib
from common import *
site = importlib.import_module("04_build_site")
R = site.R; V = R["v"]; m = R["meta"]
def fill(t):
    return re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda x: site.fmt(site.get(x.group(1)), x.group(3)), t)
# numbers written into alt text by hand: check them against results.json
assert R["dates"]["peak_year_n"] == 298 and R["cold_war"]["ew_before_1990"] == 469 and R["cold_war"]["ew_1990_1999"] == 727
assert R["top_places"][0][2] == 122 and R["top_places"][1][2] == 118 and R["country_pairs"][0][4] == 1442
assert [r[2] for r in R["ended"]["by_country"][:4]] == [29, 15, 12, 7] and R["ended"]["by_country"][3][0] == "UKR"
assert round(R["distance"]["by_decade"]["1940"]["intercontinental"] * 100) == 4 and round(R["country_story"]["JPN"]["by_decade"]["1980"][1] * 100) == 21
assert round(R["country_story"]["CHN"]["by_decade"]["2010"][1] * 100) == 17 and round(R["country_story"]["USA"]["by_decade"]["1980"][1] * 100) == 14
assert R["top_places"][2][2] == R["top_places"][3][2] and {R["top_places"][2][0], R["top_places"][3][0]} == {"Shanghai", "Kyiv"}
assert R["distance"]["by_decade"]["1980"]["median_km"] > 2 * R["distance"]["by_decade"]["1950"]["median_km"]
BL = os.path.join(ROOT, "release", "blog")
post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read())
open(os.path.join(BL, "post.html"), "w", encoding="utf-8").write(post)
for x in re.findall(r"\{\{IMG\|([^|]+)\|", post): assert os.path.exists(os.path.join(BL, x)), x
print("blog words", len(re.sub(r"<[^>]+>|\{\{IMG[^}]*\}\}", " ", post).split()))
meta = {"title": "Who is your town twinned with?", "slug": SLUG,
        "excerpt": f"I drew all {m['pairs']:,} twin town and sister city links on Wikidata as arcs on one map: a post-war European habit that peaked in 1990, reached across the Iron Curtain and out to Japan and China, and lost dozens of Russian links after 2022.",
        "seo_description": f"A map of {m['pairs']:,} twin town and sister city links from Wikidata: when they began, how far they reach, and which were cut after 2022.",
        "tags": ["twin towns", "sister cities", "maps", "Wikidata", "Europe", "Cold War", "data visualisation", "history"],
        "header_alt": f"Title card reading 'Who is your town twinned with?' on pale paper beside a world map criss-crossed by {m['pairs']:,} faint coloured arcs joining twinned towns, densest over Europe with long bundles to North America, Japan and China."}
assert len(meta["seo_description"]) < 160
json.dump(meta, open(os.path.join(BL, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

d = R["dates"]; cw = R["cold_war"]; ig = R["inner_german"]; en = R["ended"]; wc = R["wikipedia_check"]; bd = R["distance"]["by_decade"]
readme = f"""# Who is your town twinned with?

Every twin town and sister city link recorded on Wikidata (property P190, "twinned administrative body"), {m['pairs']:,} pairs between {m['places']:,} places, drawn as arcs on an interactive world map with a panel for every town: its partners and when each link began. With charts of when twinning happened, how far it reaches, the Cold War, the rise of Japan and China, namesakes, and the links ended after 2022.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- {m['pairs']:,} twinnings between {m['places']:,} places in {m['countries']} countries and territories; {d['n_dated']:,} ({round(d['share_dated']*100)}%) have a start date and {en['n']} an end date.
- New dated twinnings: {d['by_decade']['1950']} in the 1950s, {d['by_decade']['1990']:,} in the 1990s; the busiest year is {d['peak_year']} ({d['peak_year_n']}). {round(d['share_1990s_or_later']*100)}% of dated pairs began in 1990 or later.
- France and Germany are the most common pair of countries ({R['pairs_story']['FRA_DEU']['total']:,} pairs), peaking in the 1960s, when they were {V['fra_deu_60s_pct']} of all new dated links.
- East and West (Cold War camps by present-day country): {V['ew_pre90_pct']} of dated pairs begun before 1990, {V['ew_90s_pct']} of those begun in the 1990s. {ig['n']} of {ig['domestic_de']} German domestic pairs join East and West; of the {ig['dated']} dated, {ig['in_1990']} were made in 1990.
- Twins moved further apart: links between continents were {V['ic_50s_pct']} of new dated links in the 1950s and {V['ic_80s_pct']} in the 1980s (median distance {bd['1950']['median_km']} km and {bd['1980']['median_km']:,} km). Japan's share of new links peaked in the 1980s ({V['jpn_80s_pct']}); China's was {V['chn_10s_pct']} in the 2010s.
- Most-twinned: {R['top_places'][0][0]} ({R['top_places'][0][2]}), {R['top_places'][1][0]} ({R['top_places'][1][2]}); Bethlehem has {R['named']['bethlehem'][2]}, more than London, Berlin or Paris. {R['namesakes']['n']} pairs are namesakes.
- {en['since_2022_rus_blr']} twinnings with Russian ({en['rus']}) or Belarusian ({en['blr']}) places are recorded as ended since 2022, a documented minimum ({en['rus_still_open']:,} Russian pairs have no end date).
- Coverage check: {round(wc['match_share']*100)}% of {wc['lines']:,} partner lines on English Wikipedia's {wc['pages']} list pages match a Wikidata pair by name.

## Files

- `index.html`: the interactive page (Leaflet; loads `data/page.json`, `data/countries.json`, `data/towns.json`, `data/hills.png`). Arcs and town dots are drawn on a canvas layer.
- `data/pairs.csv`: every twinning as an undirected pair: Wikidata ids and names, present-day countries (ISO3), start year (earliest given), whether the two sides' start years differ, end year, end cause (Wikidata id), whether stated on both sides, great-circle distance in km.
- `data/places.csv`: every twinned place: Wikidata id, name, coordinates, country and continent (Natural Earth), German state or UK nation where relevant, population, type, number of partners.
- `data/results.json`: every number used in the page, paper, blog and collage.
- `data/page.json`: compact data for the page. `data/countries.json`, `data/towns.json`, `data/hills.png`: shared map layers (as in study-abroad and games-on-the-map).
- `data/interim/`: pair flags, prepare log, and `wikipedia_lists.json.gz` (host and partner names extracted from the English Wikipedia list pages, used for the coverage check).
- `code/`: the pipeline. `release/`: paper, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## How to rerun

Python 3 with pandas, numpy, shapely, pyproj, matplotlib, Pillow; xelatex for the paper. The two source bundles (gzipped JSON fetched in a browser from the QLever Wikidata endpoint and the English Wikipedia API on {m['retrieved']}) are read from `TT_RAW`; Natural Earth from `NE`.

```
python3 code/01_prepare.py      # bundles -> data/places.csv, data/pairs.csv, data/interim/
python3 code/02_analyse.py      # results.json
python3 code/03_page_data.py    # page.json and shared layers
python3 code/04_build_site.py   # index.html (with checks of facts stated in words)
python3 code/05_figures.py      # blog and paper figures, header.png
python3 code/06_paper.py        # paper PDF
python3 code/07_release.py      # blog post, Zenodo files, README
python3 reddit/collage.py       # Reddit collage
```

## Method in brief

All Wikidata P190 statements with start time (P580) and end time (P582) qualifiers; the two directions of a link merged into one pair, using the earlier start year where they differ; start years before 1900 treated as missing. Places with no coordinates, whole countries, and schools, parks and similar items are dropped. Countries and continents from Natural Earth by point in polygon (Russia counts as Europe, Turkey as Asia). Cold War camps use present-day countries: the Eastern bloc is the former Warsaw Pact and Soviet republics plus the five eastern German states; the West is NATO as of 1989, the western German states and Austria, Finland, Ireland, Sweden and Switzerland. Namesakes match names after removing accents and words such as "Municipality". Wikipedia list lines are matched to Wikidata pairs by normalised names, which understates the overlap.

## Sources and licences

- Wikidata (https://www.wikidata.org), P190 with P580, P582, P1534 qualifiers; P625, P17, P1082, P31, P131; queried through QLever (https://qlever.cs.uni-freiburg.de) on {m['retrieved']}. CC0 1.0.
- English Wikipedia, the {wc['pages']} pages titled "List of twin towns and sister cities in ...", wikitext via the MediaWiki API on {m['retrieved']} (revision ids in data/results.json). CC BY-SA 4.0.
- Natural Earth 1:50m admin 0 countries (public domain). Map layers shared with games-on-the-map: GeoNames cities15000 place names (CC BY 4.0) and hill shading from AWS Terrain Tiles. Optional base maps: Tiles © Esri.

Text, figures and derived data: CC BY 4.0, except `data/interim/wikipedia_lists.json.gz`, which is extracted from Wikipedia and is CC BY-SA 4.0. Code: MIT. See LICENSE.

## Citation

Hotham, T. (2026) Who is your town twinned with? The world's web of twin towns and sister cities from Wikidata. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher, ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """Licences for this repository

Text, figures, the interactive page content and derived data (data/, release/, reddit/):
Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/
The derived data come from Wikidata (CC0) and Natural Earth (public domain).
Exception: data/interim/wikipedia_lists.json.gz contains host and partner names extracted from English Wikipedia
list articles and is licensed CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), attribution: Wikipedia contributors.
Shared map layers: GeoNames place names (CC BY 4.0). Please credit the original sources as listed in README.md.

Code (code/, reddit/collage.py):

MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
pdf = "Hotham_Twin_Towns.pdf"
shutil.copy(os.path.join(ROOT, "release", pdf), Z)
for f in ["pairs.csv", "places.csv", "results.json"]:
    shutil.copy(os.path.join(DATA, f), Z)
zp = os.path.join(Z, f"{SLUG}_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for base in ["code", "data"]:
        for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
            dn[:] = [x for x in dn if x != "__pycache__"]
            for f in fn: z.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), ROOT))
    for f in ["README.md", "LICENSE"]: z.write(os.path.join(ROOT, f), f)
abstract = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", open(os.path.join(ROOT, "release", "paper", "Hotham_Twin_Towns.tex"), encoding="utf-8").read(), re.S).group(1)
abstract = abstract.replace("\\%", "%").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "Who Is Your Town Twinned With? The World's Web of Twin Towns and Sister Cities from Wikidata",
         "description_html": f"<p>{abstract}</p><p>Interactive version: {PAGE}. Data and code: {REPO}. Blog post: to follow.</p>",
         "keywords": ["town twinning", "sister cities", "twin towns", "Wikidata", "networks", "municipal diplomacy", "Cold War", "Europe", "open data", "data visualisation"],
         "licence": "cc-by-4.0",
         "related": [{"identifier": REPO, "relation": "issupplementedby", "resource_type": "software"},
                     {"identifier": PAGE, "relation": "issupplementedby", "resource_type": "other"},
                     {"identifier": "https://www.wikidata.org/wiki/Property:P190", "relation": "isderivedfrom", "resource_type": "dataset"},
                     {"identifier": "https://en.wikipedia.org/wiki/Lists_of_twin_towns_and_sister_cities", "relation": "isderivedfrom", "resource_type": "other"},
                     {"identifier": "https://www.naturalearthdata.com", "relation": "isderivedfrom", "resource_type": "dataset"}]}
assert "\\" not in zmeta["description_html"], zmeta["description_html"]
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("release done", {f: os.path.getsize(os.path.join(Z, f)) // 1024 for f in os.listdir(Z)})
