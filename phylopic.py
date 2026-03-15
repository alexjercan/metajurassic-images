import json
import logging
import os
import urllib.parse
from typing import Optional, Tuple

import requests
from rich.progress import track

logger = logging.getLogger(__name__)

PHYLOPIC_BASE_URL = "https://api.phylopic.org"
INDEX_JSON_URL = "https://raw.githubusercontent.com/alexjercan/metajurassic/refs/heads/master/src/jurassic/index.json"
IMAGES_PATH = "images"
SILHOUETTE_PATH = os.path.join(IMAGES_PATH, "silhouettes")
SILHOUETTE_SPECIES_PATH = os.path.join(SILHOUETTE_PATH, "species")


def download_dinosaur_index() -> dict:
    response = requests.get(INDEX_JSON_URL)
    response.raise_for_status()
    return response.json()


def build_phylopic_url(species: str) -> str:
    query = {
        "build": 536,
        "embed_items": "true",
        "filter_license_by": "false",
        "filter_license_nc": "false",
        "filter_license_sa": "false",
        "filter_name": species,
        "page": 0,
    }
    return f"{PHYLOPIC_BASE_URL}/images?{urllib.parse.urlencode(query)}"


def download_svg(species: str) -> Optional[Tuple[bytes, str]]:
    url = build_phylopic_url(species)

    response = requests.get(url, headers={"accept": "application/vnd.phylopic.v2+json"})
    response.raise_for_status()

    items = response.json().get("_embedded", {}).get("items", [])
    if not items:
        return None

    best_vector = None
    best_area = 0
    for item in items:
        vector_file = item.get("_links", {}).get("vectorFile")
        if vector_file is None:
            continue
        sizes = vector_file.get("sizes", "0x0")
        w, h = sizes.split("x")
        area = int(w) * int(h)
        if area > best_area:
            best_area = area
            best_vector = vector_file

    if best_vector is None:
        return None

    svg_response = requests.get(best_vector["href"])
    svg_response.raise_for_status()
    return svg_response.content, best_vector["href"]


if __name__ == "__main__":
    os.makedirs(SILHOUETTE_PATH, exist_ok=True)
    os.makedirs(SILHOUETTE_SPECIES_PATH, exist_ok=True)
    data = download_dinosaur_index()

    mapping = {}
    for species, _ in track(data["species"].items()):
        try:
            response = download_svg(species)
        except Exception as e:
            logger.error("Failed to download SVG for %s: %s", species, e)
            continue

        if response is None:
            continue

        svg_content, svg_url = response
        mapping[species] = svg_url
        with open(os.path.join(SILHOUETTE_SPECIES_PATH, f"{species}.svg"), "wb") as f:
            f.write(svg_content)

    with open(os.path.join(SILHOUETTE_PATH, "mapping.json"), "w") as fg:
        json.dump(mapping, fg, indent=2)
