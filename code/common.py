"""Shared paths and helpers for the twin-towns pipeline."""
import os, json, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
INTERIM = os.path.join(DATA, "interim")
RAW = os.environ.get("TT_RAW", "/home/claude/hist/_data18/twin-towns")
NE = os.environ.get("NE", "/home/claude/hist/_data3/ne/geojson")
BUNDLE = os.path.join(RAW, "twintowns_bundle_1029.json.gz")
REGIONS = os.path.join(RAW, "twintowns_regions_1029.json.gz")

SLUG = "twin-towns"
DOI = "10.5281/zenodo.23763153"
PAGE = "https://maps.tristanhotham.com/twin-towns/"
REPO = "https://github.com/Tristan-Hotham/twin-towns"
BLOG = "https://blog.tristanhotham.com/2026/10/29/twin-towns/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

os.makedirs(INTERIM, exist_ok=True)


def save_json(obj, path, **kw):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), **kw)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def haversine(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(min(1, a)))
