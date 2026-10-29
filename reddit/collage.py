"""Reddit collage (2400 x 3000 px): the twinning web on airmail-blue paper. Run from anywhere: python3 reddit/collage.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "code"))
import numpy as np, pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon as MPoly
from PIL import Image
from figlib import *
from common import *

R = load_json(os.path.join(DATA, "results.json")); V = R["v"]
P = pd.read_csv(os.path.join(DATA, "pairs.csv")); N = pd.read_csv(os.path.join(DATA, "places.csv")).set_index("qid")
P["sy"] = P.start_year.where((P.start_year >= 1900) & (P.start_year <= 2026)); P["era"] = [era_of(y) for y in P.sy]
BGc = "#EEF2F6"; LANDc = "#DCE2E9"; FGc = "#16202C"; MUTc = "#56606C"; RED = "#C8102E"; BLUE = "#1F3F8F"
plt.rcParams.update({"figure.facecolor": BGc, "axes.facecolor": BGc, "savefig.facecolor": BGc, "text.color": FGc})
la1 = N.lat.reindex(P.qid_a).values; lo1 = N.lon.reindex(P.qid_a).values; la2 = N.lat.reindex(P.qid_b).values; lo2 = N.lon.reindex(P.qid_b).values
ARCS = gc_arcs(la1, lo1, la2, lo2, n=30)

fig = plt.figure(figsize=(12, 15), dpi=200)
# airmail stripes along the top
sa = fig.add_axes([0, .988, 1, .012]); sa.axis("off"); sa.set_xlim(0, 100); sa.set_ylim(0, 1)
for i in range(-2, 52):
    sa.add_patch(MPoly([[i * 2, 0], [i * 2 + 1, 0], [i * 2 + 2, 1], [i * 2 + 1, 1]], color=RED if i % 2 else BLUE, lw=0))
fig.text(.04, .968, "Who is your town twinned with?", fontproperties=DISP, fontsize=46, color=FGc, va="top")
fig.text(.04, .918, f"Every twin town and sister city link on Wikidata, {R['meta']['pairs']:,} of them between {R['meta']['places']:,} places,\ndrawn along the great-circle route and coloured by the decade the link began.",
         family=SER, fontsize=15.5, color=FGc, va="top", linespacing=1.35)

# hero map
ax = fig.add_axes([0, .47, 1, .40])
draw_land(ax, fc=LANDc, ec=BGc, lw=.3)
order = [7, 6, 5, 4, 3, 2, 1, 0]; alphas = [.1, .2, .2, .2, .25, .3, .35, .45]
for k, (i, a) in enumerate(zip(order, alphas)):
    segs = [s for j in np.where(P.era.values == i)[0] for s in ARCS[j]]
    ax.add_collection(LineCollection(segs, colors=ERA[i][1], linewidths=.35, alpha=a, zorder=2 + k))
frame_world(ax)
cx = .04; cy = .468
for i, (lab, col) in enumerate(ERA):
    fig.add_artist(Line2D([cx, cx + .02], [cy, cy], transform=fig.transFigure, color=col, lw=5, solid_capstyle="round"))
    fig.text(cx + .025, cy, lab, fontsize=11, va="center", color=FGc, family=MONO)
    cx += .052 + len(lab) * .0088

# four big numbers
d = R["dates"]; bd = R["distance"]["by_decade"]; en = R["ended"]
nums = [(f"{R['pairs_story']['FRA_DEU']['total']:,}", BLUE, "French and German town pairs, the\nmost common pair of countries.\nThey peaked in the 1960s."),
        (f"{d['peak_year']}", "#C99000", f"the busiest year for new twinnings\n({d['peak_year_n']} with a start date), the year\nafter the Berlin Wall fell."),
        (f"{V['ic_50s_pct']} to {V['ic_80s_pct']}", "#0E8C84", "share of new links joining two\ncontinents, 1950s to 1980s, as\nJapan and the US reached out."),
        (f"{en['since_2022_rus_blr']}", RED, "links with Russian or Belarusian\ntowns recorded as ended since\n2022. A documented minimum.")]
for k, (big, col, small) in enumerate(nums):
    x = .04 + k * .24
    fig.text(x, .435, big, fontproperties=DISP, fontsize=34 if len(big) < 8 else 28, color=col, va="top")
    fig.text(x, .385, small, family=SER, fontsize=12, color=FGc, va="top", linespacing=1.25)

# small multiples: years, Coventry, Bethlehem
a1 = fig.add_axes([.07, .128, .39, .14])
by = {int(k): v for k, v in d["by_year"].items()}; ys = list(range(1945, d["last_main"] + 1))
a1.bar(ys, [by.get(y, 0) for y in ys], width=.85, color=[ERA[era_of(y)][1] for y in ys])
a1.spines[["top", "right", "left"]].set_visible(False); a1.spines["bottom"].set_color(MUTc); a1.tick_params(colors=MUTc, labelsize=11); a1.set_yticks([0, 100, 200, 300])
a1.grid(axis="y", color="#C9D2DC", lw=.8); a1.set_axisbelow(True)
fig.text(.04, .306, "NEW TWINNINGS BY START YEAR", family=MONO, fontsize=11, color=MUTc)
fig.text(.04, .288, f"{d['n_dated']:,} pairs with a date ({round(d['share_dated']*100)}%)", family=SER, fontsize=11.5, color=FGc)

cv = R["coventry"]; bl = R["named"]["bethlehem"]
a2 = fig.add_axes([.5, .105, .48, .175]); draw_land(a2, fc=LANDc, ec=BGc, lw=.2)
for name, iso, col in (("Coventry", "GBR", BLUE), ("Bethlehem", "PSE", RED)):
    q = N[(N.name == name) & (N.iso3 == iso)].index[0]
    m = ((P.qid_a == q) | (P.qid_b == q)).values
    a2.add_collection(LineCollection([s_ for j in np.where(m)[0] for s_ in ARCS[j]], colors=col, linewidths=1.1, alpha=.8, zorder=3))
    o = [b_ if a_ == q else a_ for a_, b_ in zip(P.qid_a[m], P.qid_b[m])]
    px, py = proj(N.lon.reindex(o).values, N.lat.reindex(o).values); a2.scatter(px, py, s=10, color=col, zorder=4, lw=0)
    x0, y0 = proj(N.lon[q], N.lat[q]); a2.scatter([x0], [y0], s=70, color=FGc, edgecolor="white", lw=1.2, zorder=5)
frame_world(a2); a2.set_xlim(-1.25e7, 1.6e7); a2.set_ylim(-4.6e6, 8.4e6)
fig.text(.505, .306, "TWO TOWNS AND THEIR TWINS", family=MONO, fontsize=11, color=MUTc)
fig.text(.505, .288, f"Coventry ({cv['n']}, first {cv['partners'][0][0]} {cv['partners'][0][2]})", family=SER, fontsize=11.5, color=BLUE)
fig.text(.755, .288, f"Bethlehem ({bl[2]}; London has {R['named']['london'][2]})", family=SER, fontsize=11.5, color=RED)

fig.text(.04, .093, f"Most-twinned: {R['top_places'][0][0]} ({R['top_places'][0][2]}), {R['top_places'][1][0]} ({R['top_places'][1][2]}), Shanghai and Kyiv ({R['top_places'][2][2]} each). {R['namesakes']['n']} pairs are namesakes, such as Boston and Boston.\n"
         f"Caveat: Wikidata is a large sample, not a census. Only {round(d['share_dated']*100)}% of pairs have a start date, and {round(R['wikipedia_check']['match_share']*100)}% of the partner lines on English Wikipedia's lists match it.",
         family=SER, fontsize=11.5, color=FGc, va="top", linespacing=1.4)
fig.text(.04, .008, f"Data: Wikidata P190 twinned administrative body, with start and end dates, retrieved {R['meta']['retrieved']} (CC0).\nEnglish Wikipedia 'List of twin towns and sister cities' pages as a check (CC BY-SA 4.0). Natural Earth (public domain).\nAnalysis and chart: Tristan Hotham, with Python and matplotlib. Interactive map: maps.tristanhotham.com/twin-towns",
         family=MONO, fontsize=9, color=MUTc, linespacing=1.45)
out = os.path.join(HERE, "twin_towns.png")
fig.savefig(out, dpi=200); plt.close(fig)
Image.open(out).convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True)
print("ok", os.path.getsize(out) // 1024, "KB")
