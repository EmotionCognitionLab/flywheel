import typing as t
from pathlib import Path

from flywheel_gear_toolkit import GearToolkitContext

AnyPath = t.Union[Path, str]


def add_tag_to_file(context: GearToolkitContext, input_file: dict, tag: str) -> None:
    """Adds a tag to a file entry"""
    parent = context.client.get(input_file["hierarchy"]["id"])

    file_obj = parent.get_file(input_file["location"]["name"])

    if tag not in file_obj.tags:
        file_obj.add_tag(tag)


def true_stem(p: Path) -> Path:
    """Strip off suffixes of nifti and nifti archives
    i.e 'sample.nii.gz' -> 'sample'
    """
    p = str(p.name)
    while True:
        if p.endswith(".nii"):
            p = p.rstrip(".nii")
        elif p.endswith(".gz"):
            p = p.rstrip(".gz")
        else:
            break
    return Path(p)


def clean_metadata(data_to_parse: dict) -> dict:
    """
    Sift through the json files that correspond with different types of scans. Keep the
    fields associated with IQMs for MRIQC. Reorder the fields for export to metadata.json
    Args:
        data_to_parse (dict): converted from original analyses' output json summaries
    Returns:
        add_metadata (dict): dictionary to append to metadata under the analysis >
        info > sorting_classifier (filename) entry
    """

    # Should be roughly 68 metrics. See https://mriqc.readthedocs.io/en/latest/measures.html
    return {
        k: v
        for k, v in data_to_parse.items()
        if (not k.startswith("__") and k not in ["bids_meta", "provenance"])
    }
