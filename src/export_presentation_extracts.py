"""Render the PowerPoint chart extracts in exhibits/presentation/ from the built dashboards.

Run after src/build_dashboards.py:

    python3 src/export_presentation_extracts.py

Each chart is drawn by the dashboard's own code in headless Chrome with a fixed set of filters,
saved as SVG, then converted to a 2x PNG with rsvg-convert (librsvg). Set CHROME to the browser
binary if it is not in the default macOS location or on PATH.
"""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
OUT = ROOT / "exhibits/presentation"

# page -> (filters applied before export, {extract name: chart container id or "js:<expression>"})
EXTRACTS = {
    "strategic_acquisition.html": (
        "get('start').value='2025-01';get('span').value='6';get('channel').value='ALL';get('age').value='365';"
        "get('model').value='A_v0.3_BASELINE';get('byChAge').value='90';get('metric').value='roas';"
        "get('payAge').value='365';get('payMeasure').value='real';draw();",
        {
            "cohort_payback": "pay",
            "customer_cohort_evolution": "js:cohortChart(cohortModel(data,state.ms,'ALL',state.model,365),true)",
            "channel_contribution_by_cohort": "byCh",
            "cohort_channel_mix": "mix",
            "channel_efficiency_comparison": "eff",
        },
    ),
    "operational_campaigns.html": (
        "get('channel').value='Paid affiliates';fillCampaigns('F1');get('start').value='2026-06-01';"
        "get('span').value='7';draw();",
        {
            "campaign_daily_spend": "chSpend",
            "campaign_cumulative_spend": "chPace",
            "campaign_registrations": "chSignups",
            "campaign_cac": "chCac",
            "campaign_activation_maturity": "chAct",
        },
    ),
}


def chrome():
    for candidate in [os.environ.get("CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                      shutil.which("google-chrome"), shutil.which("chromium")]:
        if candidate and Path(candidate).exists():
            return candidate
    raise SystemExit("Chrome not found; set CHROME to the browser binary.")


def render(page, filters, charts, browser, tmp):
    html = (SITE / page).read_text(encoding="utf-8")
    html = html.replace('<meta charset="utf-8">', f'<meta charset="utf-8"><base href="{SITE.as_uri()}/">', 1)
    # A chart is a container id, or "js:<expression>" returning SVG markup.
    dump = ("document.body.innerHTML=Object.entries(" + repr(charts) + ").map(([n,id])=>"
            "'<div data-extract=\"'+n+'\">'+(id.startsWith('js:')?eval(id.slice(3)):document.getElementById(id).innerHTML)+'</div>').join('');")
    html = html.replace("</html>", f"<script>{filters}{dump}</script></html>")
    probe = Path(tmp) / page
    probe.write_text(html, encoding="utf-8")
    dom = subprocess.run([browser, "--headless", "--disable-gpu", "--dump-dom", probe.as_uri()],
                         capture_output=True, text=True, check=True).stdout
    found = dict(re.findall(r'<div data-extract="([^"]+)">(<svg.*?</svg>)</div>', dom, re.S))
    missing = set(charts) - set(found)
    if missing:
        raise SystemExit(f"{page}: charts not rendered: {sorted(missing)}")
    return found


def main():
    browser = chrome()
    with tempfile.TemporaryDirectory() as tmp:
        for page, (filters, charts) in EXTRACTS.items():
            for name, svg in render(page, filters, charts, browser, tmp).items():
                svg_path = OUT / f"{name}.svg"
                svg_path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n", encoding="utf-8")
                subprocess.run(["rsvg-convert", "-w", "1680", "-b", "white", "-o", str(OUT / f"{name}.png"),
                                str(svg_path)], check=True)
                print("wrote", svg_path.relative_to(ROOT), "and .png")


if __name__ == "__main__":
    main()
