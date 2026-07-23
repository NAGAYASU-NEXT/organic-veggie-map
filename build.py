#!/usr/bin/env python3
"""
Build script for the 百年の春 organic vegetable map.

Reads data.json (the single source of truth for stores / producers / markets)
and renders:
  output/map.html          - A4 print version (source for the PDF)
  output/map.pdf           - A4 print PDF (via weasyprint)
  output/map_mobile.html   - mobile-friendly responsive version
  docs/index.html          - copy of the mobile version, served publicly via GitHub Pages

Usage:
    python3 build.py

To add a new store or producer, edit data.json only, then re-run this script.
Adding a store automatically:
  - inserts it into the correct area section of the store list
  - computes which producers' "取扱店" numbers include it
  - places a numbered pin on the map at the cx/cy you specify

You still need to manually choose reasonable cx/cy pixel coordinates for new
pins (see README.md for how the coordinate system works), since the map is a
hand-illustrated SVG, not a live geodata renderer.
"""
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data.json"
TEMPLATES_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "output"
DOCS_DIR = ROOT / "docs"


def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def compute_producer_stores(data):
    """For each producer, find the sorted list of store numbers that carry it."""
    producer_stores = {}
    for store in data["stores"]:
        for p in store["producers"]:
            producer_stores.setdefault(p["name"], set()).add(store["number"])
    for producers_list in (data["producers"],):
        for p in producers_list:
            nums = sorted(producer_stores.get(p["name"], []))
            p["store_numbers"] = nums
            p["store_numbers_str"] = ", ".join(str(n) for n in nums)
    return data


def group_stores_by_area(data):
    by_area = {a["id"]: [] for a in data["areas"]}
    for s in data["stores"]:
        by_area[s["area"]].append(s)
    for area_id in by_area:
        by_area[area_id].sort(key=lambda s: s["number"])
    return by_area


def build():
    data = load_data()
    data = compute_producer_stores(data)
    stores_by_area = group_stores_by_area(data)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    OUTPUT_DIR.mkdir(exist_ok=True)

    context = {
        "data": data,
        "stores_by_area": stores_by_area,
        "areas": data["areas"],
    }

    # --- Print version ---
    print_html = env.get_template("print.html.j2").render(**context)
    (OUTPUT_DIR / "map.html").write_text(print_html, encoding="utf-8")
    print("wrote output/map.html")

    try:
        from weasyprint import HTML
        HTML(string=print_html, base_url=str(OUTPUT_DIR)).write_pdf(
            str(OUTPUT_DIR / "map.pdf")
        )
        print("wrote output/map.pdf")
    except ImportError:
        print("weasyprint not installed - skipped PDF generation "
              "(pip install weasyprint --break-system-packages)")
    except OSError as e:
        print(f"weasyprint could not load its native libraries - skipped PDF generation ({e})")

    # --- Mobile version ---
    mobile_html = env.get_template("mobile.html.j2").render(**context)
    (OUTPUT_DIR / "map_mobile.html").write_text(mobile_html, encoding="utf-8")
    print("wrote output/map_mobile.html")

    # --- Public GitHub Pages copy (same content as the mobile version) ---
    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "index.html").write_text(mobile_html, encoding="utf-8")
    print("wrote docs/index.html")


if __name__ == "__main__":
    build()
