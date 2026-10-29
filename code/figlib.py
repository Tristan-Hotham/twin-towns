"""Shared drawing helpers: fonts, palette, era colours, a Robinson world map and great-circle arcs."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import PolyCollection, LineCollection
from pyproj import Transformer
from shapely.geometry import shape
from common import DATA, NE

FONT_DIR = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    p = os.path.join(FONT_DIR, f)
    if os.path.exists(p): fm.fontManager.addfont(p)
DISP = fm.FontProperties(fname=os.path.join(FONT_DIR, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG = "#F8F4EC"; FG = "#1F1B24"; MUTED = "#655F6B"; RULE = "#DED5C4"; LAND = "#EFE8DA"; SEA = "#F8F4EC"; EDGE = "#FFFFFF"
ERA = [("Before 1960", "#3B3B98"), ("1960s", "#1F78B4"), ("1970s", "#12A39A"), ("1980s", "#5E9E2E"),
       ("1990s", "#D99A00"), ("2000s", "#E8661A"), ("2010 on", "#D7263D"), ("No date", "#9A948A")]
plt.rcParams.update({"font.family": MONO, "font.size": 12, "text.color": FG, "axes.labelcolor": FG, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.edgecolor": RULE, "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})
LON0 = 11
ROB = Transformer.from_crs("EPSG:4326", f"+proj=robin +lon_0={LON0} +datum=WGS84", always_xy=True)


def era_of(y):
    if not y or y != y: return 7
    if y < 1960: return 0
    if y >= 2010: return 6
    return int((y - 1950) // 10)


def proj(lon, lat):
    lon = np.asarray(lon, float)
    lon = np.where(lon < LON0 - 180, lon + 360, np.where(lon > LON0 + 180, lon - 360, lon))
    return ROB.transform(lon, np.asarray(lat, float))


_P = None
def world_rings(simplify=0.05):
    global _P
    if _P is not None: return _P
    g = json.load(open(os.path.join(NE, "ne_50m_admin_0_countries.geojson"), encoding="utf-8"))
    out = []
    for f in g["features"]:
        p = f["properties"]
        if p["ADM0_A3"] == "ATA": continue
        iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] not in ("-99", None) else p["ADM0_A3"]
        geom = shape(f["geometry"]).simplify(simplify, preserve_topology=True)
        for q in ([geom] if geom.geom_type == "Polygon" else list(geom.geoms)):
            x, y = np.asarray(q.exterior.coords).T
            px, py = proj(x, y)
            if np.ptp(px) > 3e7: continue
            out.append((iso, np.column_stack([px, py])))
    _P = out
    return out


def draw_land(ax, fc=LAND, ec=EDGE, lw=0.3, colours=None):
    R = world_rings()
    fcs = [colours.get(i, fc) for i, _ in R] if colours else fc
    ax.add_collection(PolyCollection([r for _, r in R], facecolors=fcs, edgecolors=ec, linewidths=lw, zorder=1))


def gc_arcs(la1, lo1, la2, lo2, n=28, bow=True, kb=.1):
    """Great-circle routes for arrays of endpoints, projected to Robinson and bowed slightly northwards (as on the page).
    Returns a list of (k, m, 2) arrays split where a route crosses the map edge."""
    la1, lo1, la2, lo2 = [np.radians(np.asarray(v, float)) for v in (la1, lo1, la2, lo2)]
    a = np.stack([np.cos(la1) * np.cos(lo1), np.cos(la1) * np.sin(lo1), np.sin(la1)], 1)
    b = np.stack([np.cos(la2) * np.cos(lo2), np.cos(la2) * np.sin(lo2), np.sin(la2)], 1)
    w = np.arccos(np.clip((a * b).sum(1), -1, 1))[:, None]
    t = np.linspace(0, 1, n)[None, :]
    sw = np.where(w > 1e-9, np.sin(w), 1)
    k1 = np.where(w > 1e-9, np.sin((1 - t) * w) / sw, 1 - t); k2 = np.where(w > 1e-9, np.sin(t * w) / sw, t)
    p = k1[..., None] * a[:, None, :] + k2[..., None] * b[:, None, :]
    lat = np.degrees(np.arctan2(p[..., 2], np.hypot(p[..., 0], p[..., 1]))); lon = np.degrees(np.arctan2(p[..., 1], p[..., 0]))
    x, y = proj(lon.ravel(), lat.ravel()); x = x.reshape(lon.shape); y = y.reshape(lon.shape)
    out = []
    for i in range(len(x)):
        xi, yi = x[i], y[i]
        jump = np.where(np.abs(np.diff(xi)) > 1.2e7)[0]
        if bow and len(jump) == 0:
            cx, cy = xi[-1] - xi[0], yi[-1] - yi[0]; L = np.hypot(cx, cy) or 1
            nx, ny = -cy / L, cx / L
            if ny < 0: nx, ny = -nx, -ny
            k = L * (kb - .06 * min(1, L / 1.6e7)) * np.sin(np.pi * t[0])
            xi = xi + nx * k; yi = yi + ny * k
        segs = np.split(np.column_stack([xi, yi]), jump + 1)
        out.append([s for s in segs if len(s) > 1])
    return out


def frame_world(ax):
    ax.set_xlim(-1.25e7, 1.65e7); ax.set_ylim(-6.0e6, 8.5e6); ax.set_aspect("equal"); ax.axis("off")
