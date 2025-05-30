"""Module to test parser.py"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flywheel_gear_toolkit import GearToolkitContext

from fw_gear_mriqc.parser import parse_config

CONFIG = {
    "measurement": "auto-detect",
    "verbose_reports": True,
    "include_rating_widget": False,
    "tag": "mriqc",
    "debug": True,
}


@pytest.fixture
def nifti_path():
    return tempfile.NamedTemporaryFile(suffix=".nii").name


def test_parse_config_no_nifti_raises(nifti_path):
    """Invalid filepath reslts in FileNotFound error.
    Not mocking pathlib.Path.exists call in this test
    """
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    gear_context.config["measurement"] = "functional"
    gear_context.get_input_path.return_value = nifti_path

    with pytest.raises(FileNotFoundError):
        parse_config(gear_context)


@patch("pathlib.Path.exists")
def test_parse_config_bids_parse_functional(exists):
    """BIDS filename is first source of truth when finding measurement type.
    Measurement field is ignored when BIDS filepath passed in.
    Testing on functional scan
    """
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    # parser will reset "measurement" field based on BIDS filename
    gear_context.config["measurement"] = "not_functional"
    nifti_path = "sub-test_ses-test_task-test_acq-test_rec-test_run-1_echo-1_bold.nii"
    gear_context.get_input_path.return_value = nifti_path

    debug, gear_args = parse_config(gear_context)

    assert gear_args["nifti_path"] == Path(nifti_path)
    assert gear_args["measurement"] == "functional"
    assert gear_args["bids_compliant"]


@patch("pathlib.Path.exists")
def test_parse_config_bids_parse_anatomy(exists):
    """BIDS filename is first source of truth when finding measurement type.
    Measurement field is ignored when BIDS filepath passed in.
    Testing on anatomy scan
    """
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    # parser will reset "measurement" field based on BIDS filename
    gear_context.config["measurement"] = "not_anat"
    nifti_path = "sub-test_ses-test_acq-test_ce-test_rec-test_run-1_part-test_T1w.nii"
    gear_context.get_input_path.return_value = nifti_path

    debug, gear_args = parse_config(gear_context)

    assert gear_args["nifti_path"] == Path(nifti_path)
    assert gear_args["measurement"] == "t1"
    assert gear_args["bids_compliant"]


@patch("pathlib.Path.exists")
def test_parse_config_bids_parse_longer_filename(exists):
    """BIDS filename is truncated when it contains fields outside of regex pattern"""
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    gear_context.config["measurement"] = "not_anat"
    nifti_path = (
        "EXTRAINFO_sub-test_ses-test_acq-test_ce-test_rec-test_run-1_part-test_T1w.nii"
    )
    output_path = "sub-test_ses-test_acq-test_ce-test_rec-test_run-1_part-test_T1w.nii"
    gear_context.get_input_path.return_value = nifti_path

    debug, gear_args = parse_config(gear_context)

    assert gear_args["nifti_path"] == Path(output_path)
    assert gear_args["measurement"] == "t1"
    assert gear_args["bids_compliant"]


@patch("pathlib.Path.exists")
def test_parse_config_autodetect_functional(exists, nifti_path):
    """Functional scans correctly auto-detected as property measurement type
    given classification information (when not using BIDS format)
    """
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    gear_context.config["measurement"] = "auto-detect"
    gear_context.get_input.return_value = {
        "object": {
            "classification": {"Intent": ["Functional"], "Measurement": ["BOLD"]}
        }
    }

    gear_context.get_input_path.return_value = nifti_path

    debug, gear_args = parse_config(gear_context)

    assert gear_args["measurement"] == "functional"
    assert not gear_args["bids_compliant"]


@patch("pathlib.Path.exists")
def test_parse_config_autodetect_anatomy(exists, nifti_path):
    """Anatomy scans correctly auto-detected as property measurement type
    given classification information (when not using BIDS format)
    """
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    gear_context.config["measurement"] = "auto-detect"
    gear_context.get_input.return_value = {
        "object": {"classification": {"Intent": ["Structural"], "Measurement": ["T1"]}}
    }
    gear_context.get_input_path.return_value = nifti_path

    debug, gear_args = parse_config(gear_context)

    assert gear_args["measurement"] == "t1"
    assert not gear_args["bids_compliant"]


@patch("pathlib.Path.exists")
def test_parse_config_autodetect_no_classification_raises(exists, nifti_path):
    """Invalid classification when auto-detecting measurement type without
    BIDS format raises Runtime Error
    """
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    gear_context.config["measurement"] = "auto-detect"
    gear_context.get_input_path.return_value = nifti_path

    with pytest.raises(RuntimeError):
        parse_config(gear_context)


@patch("pathlib.Path.exists")
def test_parse_config_autodetect_incorrect_classification_raises(exists, nifti_path):
    """Invalid classification when auto-detecting measurement type without
    BIDS format raises Runtime Error
    """
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    gear_context.config["measurement"] = "auto-detect"
    gear_context.get_input.return_value = {
        "object": {"classification": {"Intent": ["wrong_string"]}}
    }
    gear_context.get_input_path.return_value = nifti_path

    with pytest.raises(RuntimeError):
        parse_config(gear_context)


@patch("pathlib.Path.exists")
def test_parse_config_incorrect_measurement_raises(exists, nifti_path):
    """Invalid measurement type without BIDS format raises Runtime Error"""
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    gear_context.config["measurement"] = "wrong_string"
    gear_context.get_input_path.return_value = nifti_path

    with pytest.raises(RuntimeError):
        parse_config(gear_context)


@patch("pathlib.Path.exists")
def test_parse_config_opts_exists(exists, nifti_path):
    exists.return_value = True
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.config = CONFIG
    gear_context.config["measurement"] = "functional"
    gear_context.config["include_rating_widget"] = False
    gear_context.get_input_path.return_value = nifti_path

    debug, gear_args = parse_config(gear_context)

    assert not gear_args["include_rating_widget"]
