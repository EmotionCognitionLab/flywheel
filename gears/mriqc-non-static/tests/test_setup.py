from pathlib import Path

from fw_gear_mriqc.setup import bids_setup, build_dir, non_bids_setup


def test_build_dir_session():
    p = build_dir(Path("work"), "sub-1", "anat", "ses-1")
    assert p == Path("work/sub-1/ses-1/anat")


def test_build_dir_no_session():
    p = build_dir(Path("work"), "sub-1", "anat")
    assert p == Path("work/sub-1/anat")


def test_bids_setup():
    s = bids_setup(Path("sub-1_ses-1_otherinfo.nii.gz"), "t1")
    assert s == ("sub-1", "ses-1", "anat", "sub-1_ses-1_otherinfo.nii.gz")


def test_bids_setup_no_ses():
    s = bids_setup(Path("sub-1_otherinfo.nii.gz"), "t1")
    assert s == ("sub-1", None, "anat", "sub-1_otherinfo.nii.gz")


def test_bids_setup_func():
    s = bids_setup(Path("sub-1_ses-1_task-task_bold.nii.gz"), "functional")
    assert s == ("sub-1", "ses-1", "func", "sub-1_ses-1_task-task_bold.nii.gz")


def test_non_bids_setup():
    s = non_bids_setup(Path("nonbids_filename.nii.gz"), "t1")
    assert s == ("sub-FLYWHLnonbids", None, "anat", "sub-FLYWHLnonbids_T1w.nii.gz")


def test_non_bids_setup_no_ses():
    s = non_bids_setup(Path("nonbids_filename.nii.gz"), "t1")
    assert s == ("sub-FLYWHLnonbids", None, "anat", "sub-FLYWHLnonbids_T1w.nii.gz")


def test_non_bids_setup_func():
    s = non_bids_setup(Path("nonbids_filename.nii.gz"), "functional")
    assert s == (
        "sub-FLYWHLnonbids",
        None,
        "func",
        "sub-FLYWHLnonbids_task-FLYWHLnonbids_bold.nii.gz",
    )
