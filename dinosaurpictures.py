""" Python Tool script that uses https://dinosaurpictures.org/*-pictures to download pictures of dinosaurs. """

import os
from typing import Optional

import bs4
import requests
from rich.progress import track

DINOSAUR_PICTURES_URL = "https://dinosaurpictures.org/{dinosaur_name}-pictures"
INDEX_JSON_URL = "https://raw.githubusercontent.com/alexjercan/metajurassic/refs/heads/master/src/jurassic/index.json"
IMAGES_PATH = "images"
IMAGES_SPECIES_PATH = os.path.join(IMAGES_PATH, "dinosaurpictures")


def download_dinosaur_index() -> dict:
    response = requests.get(INDEX_JSON_URL)
    response.raise_for_status()
    return response.json()


def download_dinosaur_pictures(dinosaur_name: str) -> Optional[str]:
    url = DINOSAUR_PICTURES_URL.format(dinosaur_name=dinosaur_name)
    response = requests.get(url)
    response.raise_for_status()

    text = response.text
    soup = bs4.BeautifulSoup(text, "html.parser")
    images = soup.find_all("img", {"title": dinosaur_name})
    for image in images:
        parent = image.parent
        if parent.name == "a":
            href = parent.get("href")
            if href is not None:
                return href

    return None


if __name__ == "__main__":
    os.makedirs(IMAGES_PATH, exist_ok=True)
    os.makedirs(IMAGES_SPECIES_PATH, exist_ok=True)
    data = download_dinosaur_index()

    for species, info in track(data["species"].items()):
        image_url = download_dinosaur_pictures(info["species"])
        if image_url is not None:
            response = requests.get(image_url)
            response.raise_for_status()

            os.makedirs(IMAGES_SPECIES_PATH, exist_ok=True)
            with open(os.path.join(IMAGES_SPECIES_PATH, f"{species}.jpg"), "wb") as f:
                f.write(response.content)
