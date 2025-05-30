import re
import typing as t
from pathlib import Path

from fw_gear_mriqc.utils import AnyPath


def build_dir(work_dir: AnyPath, subject: str, dtype: str, session=None) -> Path:
    bids_dir_structure = Path(work_dir)
    for level in [subject, session, dtype]:
        if level:
            bids_dir_structure = bids_dir_structure / level
    return bids_dir_structure


def bids_setup(
    fpath: AnyPath, measurement: str
) -> t.Tuple[str, t.Optional[str], str, str]:
    fname_str = str(fpath.name)

    subject = re.search("sub-([0-9a-zA-Z]+)", fname_str).group()

    if ses_match := re.search("ses-([0-9a-zA-Z]+)", fname_str):
        session = ses_match.group()
    else:
        session = None

    if measurement == "functional":
        dtype = "func"
    else:
        dtype = "anat"

    return subject, session, dtype, fname_str


def non_bids_setup(fpath: AnyPath, measurement: str) -> t.Tuple[str, None, str, str]:
    fname_str = str(fpath.name)

    alphanum_str = "FLYWHL" + re.search("[0-9a-zA-Z]+", fname_str).group()

    subject = "sub-" + alphanum_str

    session = None

    if measurement == "functional":
        dtype = "func"
        task = "task-" + alphanum_str
        name = subject + "_" + task + "_bold"
    else:
        dtype = "anat"
        meas_map = {"t1": "T1w", "t2": "T2w"}
        name = subject + "_" + meas_map[measurement]

    extension = "".join(fpath.suffixes)

    name += extension

    return subject, session, dtype, name
