import base64
import os

import pytest
from bs4 import BeautifulSoup

from fw_gear_mriqc.markup import embed_images, remove_rate_widget, to_data_url


@pytest.fixture(scope="session")
def image_path(tmp_path_factory):
    img_path = tmp_path_factory.mktemp("data") / "img.svg"
    with open(img_path, "wb") as f:
        f.write(os.urandom(1024))
    return img_path


@pytest.fixture(scope="session")
def html_path(tmp_path_factory, image_path):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test HTML Document</title>
    </head>
    <body>
        <img src="{image_path}" alt="Image 1">
        <img src="{image_path}" alt="Image 2">
        <object data="{image_path}" type="image/svg+xml">
        </object>
        <p><small>This is a small text.</small></p>
        <input type="checkbox" id="qcrating-toggler"></input>
        <label for="qcrating-toggler"></label>
        <div id="qcrating-menu"></div>
    </body>
    </html>
    """
    html_path = tmp_path_factory.mktemp("data") / "tmp.html"
    with open(html_path, "w") as f:
        f.write(html)
    return html_path


def test_to_data_url(image_path):
    mimetype = "svg+xml"

    result = to_data_url(image_path, mimetype)
    base64_part = result.split(",")[1]

    assert result.startswith(f"data:{mimetype};base64,")
    assert base64.b64decode(base64_part)


def test_embed_images(html_path):
    embed_images(html_path)

    with open(html_path, "r") as file:
        soup = BeautifulSoup(file.read(), "html.parser")
    img_srcs = [img["src"] for img in soup.find_all("img")]
    obj_data = [obj["data"] for obj in soup.find_all("object")]

    assert not soup.find_all("small")
    assert all([s.startswith("data:image/svg+xml;base64,") for s in img_srcs])
    assert all([d.startswith("data:image/svg+xml;base64,") for d in obj_data])


def test_remove_rate_widget(html_path):
    remove_rate_widget(html_path)

    with open(html_path, "r") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    assert not soup.find("div", {"id": "qcrating-menu"})
    assert not soup.find("input", {"id": "qcrating-toggler"})
    assert not soup.find("label", {"for": "qcrating-toggler"})
