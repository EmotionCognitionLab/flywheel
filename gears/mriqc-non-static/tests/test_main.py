"""Module to test main.py"""
import os
from pathlib import Path
from unittest.mock import MagicMock

from flywheel_gear_toolkit import GearToolkitContext

from fw_gear_mriqc.main import cleanup, run


def test_run(fs, fp):
    """Test that a run with all expected file outputs returns error code 0"""

    work_dir = Path("flywheel/v0/work")
    output_dir = Path("flywheel/v0/output")
    nifti = Path("flywheel/v0/input/nifti/sub-0_ses-0_T1w.nii.gz")

    fs.create_dir(work_dir)
    fs.create_dir(output_dir)
    fs.create_file(nifti)

    meas = "t1"

    gear_args = {
        "nifti_path": nifti,
        "measurement": meas,
        "bids_compliant": True,
        "work_dir": work_dir,
        "output_dir": output_dir,
        "verbose_reports": True,
        "include_rating_widget": True,
        "tag": "mriqc",
    }

    fp.register(
        [
            "mriqc",
            "--no-sub",
            "--verbose-reports",
            work_dir,
            output_dir / "out",
            "participant",
            "-w",
            work_dir,
            "--participant_label",
            "sub-0",
        ]
    )

    assert run(gear_args) == 0


def return_code_callback(process, code):
    process.returncode = code


def test_run_mriqc_fail(fs, fp):
    """Test that a run with failure in the MRIQC subprocess reuturns
    with error code 1"""

    work_dir = Path("flywheel/v0/work")
    output_dir = Path("flywheel/v0/output")
    nifti = Path("flywheel/v0/input/nifti/sub-0_ses-0_T1w.nii.gz")

    fs.create_dir(work_dir)
    fs.create_dir(output_dir)
    fs.create_file(nifti)

    meas = "t1"

    gear_args = {
        "nifti_path": nifti,
        "measurement": meas,
        "bids_compliant": True,
        "work_dir": work_dir,
        "output_dir": output_dir,
        "verbose_reports": True,
        "include_rating_widget": True,
        "tag": "mriqc",
    }

    fp.register(
        [
            "mriqc",
            "--no-sub",
            "--verbose-reports",
            work_dir,
            output_dir / "out",
            "participant",
            "-w",
            work_dir,
            "--participant_label",
            "sub-0",
        ],
        callback=return_code_callback,
        callback_kwargs={"code": 1},
    )

    assert run(gear_args) == 1


def test_cleanup(fs):
    mock_context = MagicMock(spec=GearToolkitContext)

    work_dir = Path("flywheel/v0/work")
    output_dir = Path("flywheel/v0/output")
    nifti = Path("flywheel/v0/input/nifti/sub-0_ses-0_T1w.nii.gz")
    json = output_dir / "out" / "sub-0/ses-0/anat/sub-0_ses-0_T1w.json"
    html = output_dir / "out" / "sub-0_ses-0_T1w.html"
    svg = output_dir / "out" / "sub-0/figures/img.svg"

    fs.create_dir(work_dir)
    fs.create_dir(output_dir)
    fs.create_file(nifti)

    fs.create_file(
        svg,
        contents='<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg"/>',
    )
    fs.create_file(json, contents='{"meta": "data"}')
    fs.create_file(html, contents="<!DOCTYPE html><title></title>")

    mock_context.mock_add_spec(
        [
            "update_file_metadata",
            "output_dir",
            "get_input_filename",
            "config",
            "metadata",
            "get_input_file_object",
        ]
    )
    mock_context.output_dir = output_dir
    mock_context.get_input_filename.return_value = nifti.name
    mock_context.metadata.add_gear_info.return_value = None

    cleanup(mock_context)

    assert any([s.endswith(".zip") for s in os.listdir(output_dir)])
    mock_context.update_file_metadata.assert_called()


def test_cleanup_no_metrics(fs):
    mock_context = MagicMock(spec=GearToolkitContext)

    work_dir = Path("flywheel/v0/work")
    output_dir = Path("flywheel/v0/output")
    nifti = Path("flywheel/v0/input/nifti/sub-0_ses-0_T1w.nii.gz")
    html = output_dir / "out" / "sub-0_ses-0_T1w.html"
    svg = output_dir / "out" / "sub-0/figures/img.svg"

    fs.create_dir(work_dir)
    fs.create_dir(output_dir)
    fs.create_file(nifti)

    fs.create_file(
        svg,
        contents='<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg"/>',
    )
    fs.create_file(html, contents="<!DOCTYPE html><title></title>")

    mock_context.mock_add_spec(
        [
            "update_file_metadata",
            "output_dir",
            "get_input_filename",
            "config",
            "metadata",
            "get_input_file_object",
        ]
    )
    mock_context.output_dir = output_dir
    mock_context.get_input_filename.return_value = nifti.name
    mock_context.update_file_metadata.return_value = None

    cleanup(mock_context)
    assert any([s.endswith(".zip") for s in os.listdir(output_dir)])
    mock_context.update_file_metadata.assert_not_called()


def test_cleanup_no_html(fs):
    mock_context = MagicMock(spec=GearToolkitContext)

    work_dir = Path("flywheel/v0/work")
    output_dir = Path("flywheel/v0/output")
    nifti = Path("flywheel/v0/input/nifti/sub-0_ses-0_T1w.nii.gz")
    json = output_dir / "out" / "sub-0/ses-0/anat/sub-0_ses-0_T1w.json"

    fs.create_dir(work_dir)
    fs.create_dir(output_dir)
    fs.create_file(nifti)

    fs.create_file(json, contents='{"meta": "data"}')

    mock_context.mock_add_spec(
        [
            "update_file_metadata",
            "output_dir",
            "get_input_filename",
            "config",
            "metadata",
            "get_input_file_object",
        ]
    )
    mock_context.output_dir = output_dir
    mock_context.get_input_filename.return_value = nifti.name
    mock_context.update_file_metadata.return_value = None

    cleanup(mock_context)
    print(os.listdir(output_dir))

    assert not any([s.endswith(".zip") for s in os.listdir(output_dir)])
    mock_context.update_file_metadata.assert_called()
