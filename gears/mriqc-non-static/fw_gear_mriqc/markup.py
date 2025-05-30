import base64
import shutil
import typing as t
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup

from fw_gear_mriqc.utils import AnyPath


def to_data_url(img_path: AnyPath, mimetype: str) -> str:
    """
    Returns encoding of image pointed to by 'img_path' as an HTML data URL.
    This allows images to be embedded into an HTML document inline.
    See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs

    Args:
        img_path (AnyPath): path to image (from HTML image tag)
        mimetype (str): image mimetype
    Returns:
        str: data URL
    """

    url = f"data:{mimetype};base64,"
    with open(img_path, "rb") as img:
        txt = img.read()
    url += (base64.b64encode(txt)).decode("utf-8")
    return url


def embed_images(
    html_path: AnyPath,
    root_dir: t.Optional[AnyPath] = None,
    mimetype: str = "image/svg+xml",
    remove_small: bool = True,
) -> None:
    """
    Replaces all src URLs in HTML image tags with data URLS.
    The original HTML file is overwritten with these modifications.
    Performs the same action on objects with the same mimetype as the images.
    Removes all <small> tags, these are used in mriqc as links to images (no longer necessary)

    Args:
        html_path (AnyPath): path to HTML file
        root_dir (AnyPath | None): All image filepaths considered relative to this directory.
                                    If None, image filepaths are considered to be absolute.
        remove_small (bool): Remove all <small> tags from the document (in mriqc used to remove
                                all broken links from HTML files)
    Returns:
        None: HTML file modified in place
    """

    with open(html_path, "r") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    for img in soup.find_all("img"):
        if img.has_attr("src"):
            if root_dir:
                src_url = Path(root_dir) / Path(img["src"])
            else:
                src_url = Path(img["src"])
            img["src"] = to_data_url(src_url, mimetype)

    for obj in soup.find_all("object", {"type": mimetype}):
        if obj.has_attr("data"):
            if root_dir:
                src_url = Path(root_dir) / Path(obj["data"])
            else:
                src_url = Path(obj["data"])
            obj["data"] = to_data_url(src_url, mimetype)

    if remove_small:
        for small_tag in soup.find_all("small"):
            small_tag.decompose()

    with open(html_path, "w") as file:
        file.write(str(soup))


def remove_rate_widget(html_path: AnyPath) -> None:
    """
    Removes widget from mriqc HTML report.

    Args:
        html_path (AnyPath): path to HTML file
    Returns:
        None: HTML file modified in place
    """
    # Convert the path to a pathlib and break to parts
    html_path = Path(html_path)
    html_dir = html_path.parent
    html_name = html_path.name
    html_backup = Path(html_dir / (html_name + ".bk"))

    try:
        # First make a backup of the file
        shutil.copy(html_path, html_backup)

        # Open and read in the html file
        html_file = open(html_path, "r")
        html_doc = html_file.read()
        html_file.close()

        # Parse the html file using beautiful soup
        soup = BeautifulSoup(html_doc, "html.parser")

        # Remove the rating menu itself
        rating_menu = soup.find("div", {"id": "qcrating-menu"})
        rating_menu.replace_with("")

        # Remove the button that toggles the rating menu (just to avoid confusion)
        rating_toggler = soup.find("input", {"id": "qcrating-toggler"})
        rating_toggler.replace_with("")

        # Remove the the rating menu text (just to avoid confusion)
        rating_toggler = soup.find("label", {"for": "qcrating-toggler"})
        rating_toggler.replace_with("")

        # Remove the old html file
        html_path.unlink()

        html = soup.prettify("utf-8")
        with open(html_path, "wb") as file:
            file.write(html)

        # If this all worked fine, remove the backup
        html_backup.unlink()

    except Exception as e:
        # Error processing file...just restore the old one
        html_path.unlink()
        shutil.copy(html_backup, html_path)
        html_backup.unlink()
        raise e


def zip_html_with_svg(html_path: Path, figures_dir: Path) -> Path:
    tmp_dir = html_path.parent
    html_dir = tmp_dir / Path(html_path.stem)
    html_dir.mkdir()

    with open(html_path, "r") as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    for img in soup.find_all("img"):
        img_path = Path(img["src"])
        shutil.copyfile(tmp_dir / img_path, html_dir / img_path.name)
        img["src"] = img_path.name

    for obj in soup.find_all("object", {"type": "image/svg+xml"}):
        if obj.has_attr("data"):
            obj_path = Path(obj["data"])
            shutil.copyfile(tmp_dir / obj_path, html_dir / obj_path.name)
            obj["data"] = obj_path.name

    # Renamed html file required by Flywheel UI viewer
    html_path.rename(html_dir / "index.html")

    zip_path = html_dir.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        for file in html_dir.glob("*"):
            if file.is_file():
                zip_file.write(file, file.name)

    return zip_path
