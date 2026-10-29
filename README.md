# Who is your town twinned with?

Every twin town and sister city link recorded on Wikidata (property P190, "twinned administrative body"), 29,437 pairs between 19,976 places, drawn as arcs on an interactive world map with a panel for every town: its partners and when each link began. With charts of when twinning happened, how far it reaches, the Cold War, the rise of Japan and China, namesakes, and the links ended after 2022.

Interactive version: https://maps.tristanhotham.com/twin-towns/
Paper: https://doi.org/10.5281/zenodo.23763153
Blog post: https://blog.tristanhotham.com/2026/10/29/twin-towns/

## Headline results

- 29,437 twinnings between 19,976 places in 208 countries and territories; 10,292 (35%) have a start date and 254 an end date.
- New dated twinnings: 257 in the 1950s, 2,558 in the 1990s; the busiest year is 1990 (298). 69% of dated pairs began in 1990 or later.
- France and Germany are the most common pair of countries (1,442 pairs), peaking in the 1960s, when they were 23% of all new dated links.
- East and West (Cold War camps by present-day country): 15% of dated pairs begun before 1990, 28% of those begun in the 1990s. 654 of 771 German domestic pairs join East and West; of the 117 dated, 52 were made in 1990.
- Twins moved further apart: links between continents were 14% of new dated links in the 1950s and 44% in the 1980s (median distance 776 km and 1,775 km). Japan's share of new links peaked in the 1980s (21%); China's was 17% in the 2010s.
- Most-twinned: Rio de Janeiro (122), Saint Petersburg (118); Bethlehem has 64, more than London, Berlin or Paris. 130 pairs are namesakes.
- 90 twinnings with Russian (80) or Belarusian (10) places are recorded as ended since 2022, a documented minimum (1,650 Russian pairs have no end date).
- Coverage check: 56% of 34,971 partner lines on English Wikipedia's 85 list pages match a Wikidata pair by name.

## Files

- `index.html`: the interactive page (Leaflet; loads `data/page.json`, `data/countries.json`, `data/towns.json`, `data/hills.png`). Arcs and town dots are drawn on a canvas layer.
- `data/pairs.csv`: every twinning as an undirected pair: Wikidata ids and names, present-day countries (ISO3), start year (earliest given), whether the two sides' start years differ, end year, end cause (Wikidata id), whether stated on both sides, great-circle distance in km.
- `data/places.csv`: every twinned place: Wikidata id, name, coordinates, country and continent (Natural Earth), German state or UK nation where relevant, population, type, number of partners.
- `data/results.json`: every number used in the page, paper, blog and collage.
- `data/page.json`: compact data for the page. `data/countries.json`, `data/towns.json`, `data/hills.png`: shared map layers (as in study-abroad and games-on-the-map).
- `data/interim/`: pair flags, prepare log, and `wikipedia_lists.json.gz` (host and partner names extracted from the English Wikipedia list pages, used for the coverage check).
- `code/`: the pipeline. `release/`: paper, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## How to rerun

Python 3 with pandas, numpy, shapely, pyproj, matplotlib, Pillow; xelatex for the paper. The two source bundles (gzipped JSON fetched in a browser from the QLever Wikidata endpoint and the English Wikipedia API on 2026-10-29) are read from `TT_RAW`; Natural Earth from `NE`.

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

- Wikidata (https://www.wikidata.org), P190 with P580, P582, P1534 qualifiers; P625, P17, P1082, P31, P131; queried through QLever (https://qlever.cs.uni-freiburg.de) on 2026-10-29. CC0 1.0.
- English Wikipedia, the 85 pages titled "List of twin towns and sister cities in ...", wikitext via the MediaWiki API on 2026-10-29 (revision ids in data/results.json). CC BY-SA 4.0.
- Natural Earth 1:50m admin 0 countries (public domain). Map layers shared with games-on-the-map: GeoNames cities15000 place names (CC BY 4.0) and hill shading from AWS Terrain Tiles. Optional base maps: Tiles © Esri.

Text, figures and derived data: CC BY 4.0, except `data/interim/wikipedia_lists.json.gz`, which is extracted from Wikipedia and is CC BY-SA 4.0. Code: MIT. See LICENSE.

## Citation

Hotham, T. (2026) Who is your town twinned with? The world's web of twin towns and sister cities from Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23763153

Dr Tristan Hotham, Independent researcher, ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
