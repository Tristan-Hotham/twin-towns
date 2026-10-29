"""Step 5: static figures for the blog (release/blog/b_*.png, 1520 px wide), the paper (release/paper/f_*.png) and header.png."""
import os
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
from PIL import Image
from figlib import *
from common import *

R = load_json(os.path.join(DATA, "results.json")); V = R["v"]
P = pd.read_csv(os.path.join(DATA, "pairs.csv")); N = pd.read_csv(os.path.join(DATA, "places.csv")).set_index("qid")
FL = pd.read_csv(os.path.join(INTERIM, "pair_flags.csv")); P["ew"] = FL.ew; P["ns"] = FL.namesake
P["sy"] = P.start_year.where((P.start_year >= 1900) & (P.start_year <= 2026))
P["era"] = [era_of(y) for y in P.sy]
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
la1 = N.lat.reindex(P.qid_a).values; lo1 = N.lon.reindex(P.qid_a).values
la2 = N.lat.reindex(P.qid_b).values; lo2 = N.lon.reindex(P.qid_b).values
ARCS = gc_arcs(la1, lo1, la2, lo2, n=30)


def arcs_by(mask_order, ax, lw, alphas, cols, z0=2):
    for k, (mask, col, a) in enumerate(zip(mask_order, cols, alphas)):
        segs = [s for i in np.where(mask)[0] for s in ARCS[i]]
        ax.add_collection(LineCollection(segs, colors=col, linewidths=lw, alpha=a, zorder=z0 + k, capstyle="round"))


def era_legend(fig, x0, y, w, fs, counts=True):
    cnt = P.era.value_counts()
    for i, (lab, col) in enumerate(ERA):
        cx = x0 + i * w / len(ERA)
        fig.add_artist(Line2D([cx, cx + .022], [y, y], transform=fig.transFigure, color=col, lw=4, solid_capstyle="round"))
        fig.text(cx + .028, y, f"{lab}" + (f"\n{cnt.get(i, 0):,}" if counts else ""), fontsize=fs, va="center", color=FG, linespacing=1.15)


def world_map(ax, lw=.32):
    draw_land(ax)
    order = [7, 6, 5, 4, 3, 2, 1, 0]           # undated first, then newest to oldest so the older, rarer links sit on top
    masks = [(P.era == i).values for i in order]
    cols = [ERA[i][1] for i in order]
    alphas = [.1, .2, .2, .2, .25, .3, .35, .45]
    arcs_by(masks, ax, lw, alphas, cols)
    frame_world(ax)


# 1. the web, coloured by start decade
for out, W, dpi in ((os.path.join(BL, "b_map.png"), 15.2, 100), (os.path.join(PA, "f_map.png"), 12, 200)):
    fig = plt.figure(figsize=(W, W * .6)); ax = fig.add_axes([0, .1, 1, .9])
    world_map(ax, lw=.32 if W > 13 else .22)
    era_legend(fig, .03, .055, .96, 12.5 if W > 13 else 9.5)
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 2. by start year
by = {int(k): v for k, v in R["dates"]["by_year"].items()}
for out, sz, dpi in ((os.path.join(BL, "b_years.png"), (15.2, 6.2), 100), (os.path.join(PA, "f_years.png"), (10, 4.2), 200)):
    fig, ax = plt.subplots(figsize=sz); fig.subplots_adjust(.06, .1, .98, .95)
    ys = [y for y in range(1945, R["dates"]["last_main"] + 1)]
    ax.bar(ys, [by.get(y, 0) for y in ys], width=.85, color=[ERA[era_of(y)][1] for y in ys])
    py = R["dates"]["peak_year"]; ax.annotate(f"{py}: {by[py]:,}", (py, by[py]), (py - 14, by[py] * 1.0), fontsize=12 if sz[0] > 12 else 9.5, va="center", ha="right", arrowprops=dict(arrowstyle="-", color=FG, lw=.8))
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True); ax.set_xlim(1944, ys[-1] + 1)
    ax.set_ylabel("new twinnings with a start date")
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 3. share of each decade's new links, named country pairs
decs = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
def end_labels(ax, ends, gap, fs, x):
    ends.sort(); last = -1e9
    for v, n, c in ends:
        v2 = max(v, last + gap); last = v2
        ax.annotate(n, (x, v), (x + 2.5, v2), color=c, fontsize=fs, weight="bold", va="center", annotation_clip=False, arrowprops=dict(arrowstyle="-", color=c, lw=.7))
for out, sz, dpi in ((os.path.join(BL, "b_pairs.png"), (15.2, 6.6), 100), (os.path.join(PA, "f_pairs.png"), (10, 4.6), 200)):
    fig, ax = plt.subplots(figsize=sz); fig.subplots_adjust(.07, .1, .76, .96)
    ends = []
    for k, n, c in [("FRA_DEU", "France and Germany", "#1F5FAD"), ("FRA_GBR", "France and UK", "#D7263D"), ("DEU_GBR", "Germany and UK", "#D99A00"), ("DEU_POL", "Germany and Poland", "#12A39A"), ("JPN_USA", "Japan and US", "#C2185B")]:
        v = [R["pairs_story"][k]["by_decade"][str(d)][1] for d in decs]
        ax.plot(decs, v, color=c, lw=2.8, marker="o", ms=5); ends.append([v[-1], n, c])
    end_labels(ax, ends, .012, 12.5 if sz[0] > 12 else 9.5, decs[-1])
    ax.set_xticks(decs); ax.set_xticklabels([f"{d}s" for d in decs]); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0%}")
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color=RULE, lw=.8); ax.set_ylim(0, None)
    ax.set_ylabel("share of the decade's new dated twinnings")
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 4. Europe: links across the Iron Curtain, two periods, land tinted by camp (present-day countries; Germany left neutral)
EASTC = {"RUS", "UKR", "BLR", "MDA", "EST", "LVA", "LTU", "GEO", "ARM", "AZE", "KAZ", "POL", "CZE", "SVK", "HUN", "ROU", "BGR"}
WESTC = {"USA", "CAN", "GBR", "FRA", "BEL", "NLD", "LUX", "NOR", "DNK", "ISL", "ITA", "PRT", "GRC", "TUR", "ESP", "AUT", "CHE", "SWE", "FIN", "IRL"}
tint = {**{c: "#F3DCE3" for c in EASTC}, **{c: "#DCE6F2" for c in WESTC}, "DEU": "#E6E1EC"}
ew = P.ew.values == 1
panels = [("Begun before 1990", ew & (P.sy < 1990).values, "#1F5FAD", R["cold_war"]["ew_before_1990"]),
          ("Begun in the 1990s", ew & ((P.sy >= 1990) & (P.sy < 2000)).values, "#C2185B", R["cold_war"]["ew_1990_1999"])]
x0, y0 = proj(-10, 40.5); x1, y1 = proj(42, 70.5)
for out, W, dpi in ((os.path.join(BL, "b_iron.png"), 15.2, 100), (os.path.join(PA, "f_iron.png"), 10, 180)):
    fig, axs = plt.subplots(1, 2, figsize=(W, W * .52)); fig.subplots_adjust(.005, .08, .995, .93, .02)
    fs = 13 if W > 13 else 9
    for ax, (title, m, col, n) in zip(axs, panels):
        draw_land(ax, lw=.5, colours=tint, ec="#FFFFFF")
        arcs_by([m], ax, .8 if W > 13 else .5, [.5], [col], z0=4)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{title}: {n:,} dated East and West links", fontsize=fs + 1, loc="left", color=col, weight="bold")
    fig.text(.01, .035, "Land tinted by camp, using present-day countries: Eastern bloc (rose), NATO members of 1989 and western neutrals (blue), Germany (lilac).", fontsize=fs - 1, color=MUTED)
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 5. reach: intercontinental share; Japan and China
bd = R["distance"]["by_decade"]; cs = R["country_story"]
for out, sz, dpi in ((os.path.join(BL, "b_reach.png"), (15.2, 6.2), 100), (os.path.join(PA, "f_reach.png"), (10, 4.4), 200)):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=sz); fig.subplots_adjust(.06, .12, .86, .84, .42)
    fs = 12.5 if sz[0] > 12 else 9
    d2 = [1940] + decs
    a1.plot(d2, [bd[str(d)]["intercontinental"] for d in d2], color="#C2185B", lw=2.8, marker="o", ms=5)
    for d in (1950, 1980, 2010):
        a1.annotate(f"{bd[str(d)]['median_km']:,} km", (d, bd[str(d)]["intercontinental"]), (0, 10), textcoords="offset points", ha="center", fontsize=fs - 1.5, color=MUTED)
    a1.set_title("Share of new dated links between continents\n(labels: median distance)", fontsize=fs, loc="left", pad=14)
    ends = []
    for k, n, c in [("JPN", "Japan", "#C2185B"), ("CHN", "China", "#D99A00"), ("USA", "United States", "#1F5FAD")]:
        v = [cs[k]["by_decade"][str(d)][1] for d in decs]; a2.plot(decs, v, color=c, lw=2.8, marker="o", ms=5); ends.append([v[-1], n, c])
    end_labels(a2, ends, .012, fs, decs[-1])
    a2.set_title("Share of new dated links that\ninclude the country", fontsize=fs, loc="left", pad=14)
    for a, dd in ((a1, d2), (a2, decs)):
        a.set_xticks(dd[::2]); a.set_xticklabels([f"{d}s" for d in dd[::2]]); a.yaxis.set_major_formatter(lambda v, p: f"{v:.0%}")
        a.spines[["top", "right"]].set_visible(False); a.grid(axis="y", color=RULE, lw=.8); a.set_ylim(0, None)
    a1.yaxis.set_major_locator(MultipleLocator(.1)); a2.yaxis.set_major_locator(MultipleLocator(.05))
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 6. champions: places and country pairs
SN = {"United Kingdom": "UK", "United States": "US"}
for out, sz, dpi in ((os.path.join(BL, "b_top.png"), (15.2, 7.4), 100), (os.path.join(PA, "f_top.png"), (10, 5.4), 200)):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=sz); fig.subplots_adjust(.16, .06, .98, .93, .75)
    fs = 12 if sz[0] > 12 else 8.5
    tp = R["top_places"][:15]; yy = np.arange(len(tp))[::-1]
    a1.barh(yy, [r[2] for r in tp], color="#1F5FAD"); a1.set_yticks(yy); a1.set_yticklabels([f"{r[0]}" for r in tp], fontsize=fs)
    for y, r in zip(yy, tp): a1.text(r[2] + 1, y, str(r[2]), va="center", fontsize=fs - 1, color=MUTED)
    a1.set_title("Most partners", fontsize=fs + 1, loc="left")
    cp = R["country_pairs"][:15]
    a2.barh(yy, [r[4] for r in cp], color="#12A39A"); a2.set_yticks(yy)
    a2.set_yticklabels([("within " + SN.get(r[2], r[2])) if r[0] == r[1] else f"{SN.get(r[2], r[2])} and {SN.get(r[3], r[3])}" for r in cp], fontsize=fs)
    for y, r in zip(yy, cp): a2.text(r[4] + 15, y, f"{r[4]:,}", va="center", fontsize=fs - 1, color=MUTED)
    a2.set_title("Most common pairs of countries", fontsize=fs + 1, loc="left")
    for a in (a1, a2): a.spines[["top", "right"]].set_visible(False); a.tick_params(axis="x", labelsize=fs - 1); a.margins(x=.12)
    fig.savefig(out, dpi=dpi); plt.close(fig)

# 7. ended since 2022 (blog) and the Wikipedia check (paper)
eb = R["ended"]["by_country"][:10]
fig, ax = plt.subplots(figsize=(15.2, 5.6)); fig.subplots_adjust(.16, .08, .97, .97)
yy = np.arange(len(eb))[::-1]; ax.barh(yy, [r[2] for r in eb], color="#C2185B"); ax.set_yticks(yy); ax.set_yticklabels([r[1] for r in eb], fontsize=13)
for y, r in zip(yy, eb): ax.text(r[2] + .3, y, str(r[2]), va="center", fontsize=12, color=MUTED)
ax.spines[["top", "right"]].set_visible(False); ax.set_xlabel("Russian or Belarusian twinnings recorded as ended since 2022, by partner country")
fig.savefig(os.path.join(BL, "b_ended.png"), dpi=100); plt.close(fig)
pp = R["wikipedia_check"]["per_page"]
fig, ax = plt.subplots(figsize=(10, 7.6)); fig.subplots_adjust(.25, .09, .97, .98)
yy = np.arange(len(pp)); ax.barh(yy, [r[2] for r in pp], color="#1F5FAD", height=.75); ax.set_yticks(yy); ax.set_yticklabels([f"{r[0]} ({r[1]:,})" for r in pp], fontsize=7.5)
ax.axvline(R["wikipedia_check"]["match_share"], color="#D7263D", lw=1); ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0%}"); ax.set_xlim(0, 1)
ax.spines[["top", "right"]].set_visible(False); ax.set_xlabel("share of list lines matched to a Wikidata pair by name")
fig.savefig(os.path.join(PA, "f_check.png"), dpi=200); plt.close(fig)

# header.png 1200x630
fig = plt.figure(figsize=(12, 6.3)); ax = fig.add_axes([.375, .06, .62, .88])
world_map(ax, lw=.22)
fig.text(.035, .88, "Who is your\ntown twinned\nwith?", fontproperties=DISP, fontsize=35, va="top", color=FG, linespacing=.95)
fig.text(.035, .42, f"{R['meta']['pairs']:,} twin town and\nsister city links on\nWikidata, coloured by\nthe decade they began.", family=SER, fontsize=14, va="top", color=FG, linespacing=1.3)
fig.text(.035, .06, "maps.tristanhotham.com/twin-towns", fontsize=10, color=MUTED)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100); plt.close(fig)
# shrink the arc maps: 256-colour palette PNGs are a fraction of the size and look the same
for p in [os.path.join(BL, "b_map.png"), os.path.join(BL, "b_iron.png"), os.path.join(PA, "f_map.png"), os.path.join(PA, "f_iron.png"), os.path.join(ROOT, "header.png")]:
    Image.open(p).convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(p, optimize=True)
print("figures done")
