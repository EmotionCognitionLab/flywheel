from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fw_gear_mriqc.utils import add_tag_to_file, true_stem


@pytest.fixture
def output_dir(tmp_path):
    # Create a temporary directory for the flywheel output
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


def test_add_tag_to_file(mock_context):
    input_file = MagicMock()
    add_tag_to_file(mock_context, input_file, "test")
    mock_context.client.get().get_file().add_tag.assert_called_with("test")


def test_true_stem_single_suffix():
    fpath = Path("file.nii")
    assert true_stem(fpath) == Path("file")


def test_true_stem_multiple_suffixes():
    fpath = Path("file.nii.gz")
    assert true_stem(fpath) == Path("file")


def test_true_stem_full_path():
    fpath = Path("dir1/dir2/file.nii.gz")
    assert true_stem(fpath) == Path("file")
