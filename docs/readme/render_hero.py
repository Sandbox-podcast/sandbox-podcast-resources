"""Render the README banner from its SVG source and the existing SANDBOX logo."""

from base64 import b64encode
from pathlib import Path
import xml.etree.ElementTree as ET

from playwright.sync_api import sync_playwright


def main() -> None:
    folder = Path(__file__).resolve().parent
    source = folder / "hero.svg"
    svg = ET.fromstring(source.read_text(encoding="utf-8"))
    width, height = int(svg.attrib["width"]), int(svg.attrib["height"])

    # SVG images cannot load sibling files when embedded as an HTML image.
    # Inline the original logo in memory; keep the editable SVG source readable.
    for node in svg.iter("{http://www.w3.org/2000/svg}image"):
        logo = (folder / node.attrib["href"]).resolve()
        data = b64encode(logo.read_bytes()).decode("ascii")
        node.set("href", f"data:image/png;base64,{data}")

    ET.register_namespace("", "http://www.w3.org/2000/svg")
    data = b64encode(ET.tostring(svg, encoding="utf-8")).decode("ascii")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        page.set_content(
            '<body style="margin:0">'
            f'<img src="data:image/svg+xml;base64,{data}" width="{width}" height="{height}">'
        )
        page.locator("img").evaluate("image => image.decode()")
        page.locator("img").screenshot(path=str(folder / "hero.png"), omit_background=True)
        browser.close()
    print(f"Rendered {folder / 'hero.png'} ({width}x{height})")


if __name__ == "__main__":
    main()
