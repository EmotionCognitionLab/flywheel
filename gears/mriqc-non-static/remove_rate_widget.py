#!/usr/bin/env python3.8
import pathlib
import shutil
import sys

from bs4 import BeautifulSoup


def main(html_path):
    # Convert the path to a pathlib and break to parts
    html_path = pathlib.Path(html_path)
    html_dir = html_path.parent
    html_name = html_path.name
    html_backup = pathlib.Path(html_dir / (html_name + ".bk"))

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
        rating_menu = soup.find("div", {"id": "rating-menu"})
        rating_menu.replace_with("")

        # Remove the button that toggles the rating menu (just to avoid confusion)
        rating_toggler = soup.find("a", {"id": "rating-toggler"})
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Requires a single html file as input")
    else:
        main(sys.argv[1])
