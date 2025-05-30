"""Main module."""
import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

from flywheel_gear_toolkit import GearToolkitContext

from fw_gear_mriqc.markup import remove_rate_widget, zip_html_with_svg
from fw_gear_mriqc.setup import bids_setup, build_dir, non_bids_setup
from fw_gear_mriqc.utils import clean_metadata, true_stem

log = logging.getLogger(__name__)


def run(gear_args: dict):
    """Runs MRIQC algorithm on input nifti for quality assessment of MRI.

    Returns:
        int: error code
        (dict | None): mriqc metrics or None
    """
    log.debug("This is the beginning of the run file")

    nifti_path = gear_args["nifti_path"]
    measurement = gear_args["measurement"]
    bids_compliant = gear_args["bids_compliant"]

    work_dir = gear_args["work_dir"]
    output_dir = gear_args["output_dir"]
    tmp_dir = output_dir / "out"

    verbose_reports = gear_args["verbose_reports"]

    # Create BIDS directory
    setup = bids_setup if bids_compliant else non_bids_setup
    subject, session, dtype, fname = setup(nifti_path, measurement)
    bids_dir = build_dir(work_dir, subject, dtype, session)
    bids_dir.mkdir(parents=True)
    log.debug(f"Built BIDS directory structure: {bids_dir}")

    # Copy nifti file to BIDS directory
    shutil.copyfile(nifti_path, bids_dir / fname)

    # Create a dataset_description.json file
    with open(work_dir / "dataset_description.json", "w") as fp:
        json.dump({"Name": "MRIQC", "License": "", "BIDSVersion": "1.0.0"}, fp)

    # RUN MRIQC
    cmd = [
        "mriqc",
        "--no-sub",
        work_dir,
        tmp_dir,
        "participant",
        "-w",
        work_dir,
        "--participant_label",
        subject,
    ]

    if verbose_reports:
        cmd.insert(2, "--verbose-reports")

    log.info("Starting to run MRIQC")
    start = time.time()
    mriqc_run = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Continuously read the output and error streams and log them
    log.debug("MRIQC output:")
    for line in mriqc_run.stdout:
        log.debug(line.decode("utf-8").strip())

    # Wait for the subprocess to finish
    mriqc_run.wait()
    elapsed = time.time() - start
    log.info(f"MRIQC completed in {elapsed} seconds")

    if mriqc_run.returncode != 0:
        log.error(
            f"MRIQC failed with return code {mriqc_run.returncode} after {elapsed}s"
        )
        return 1

    return 0


def cleanup(context: GearToolkitContext):
    tmp_dir = context.output_dir / "out"
    stem = true_stem(Path(context.get_input_filename("nifti")))

    # Optionally add tag to file
    if tag := context.config.get("tag"):
        context.metadata.add_file_tags(context.get_input_filename("nifti"), tag)

    # Parse metadata json file and upload
    try:
        json_path = next(tmp_dir.glob("sub*/**/*.json"))
        with open(json_path, "r") as f:
            metadata = {"derived": {"IQM": clean_metadata(json.load(f))}}
        context.update_file_metadata(
            context.get_input_filename("nifti"), False, info=metadata
        )
    except Exception as e:
        json_path = None
        log.exception("Error parsing JSON metadata file. Skipping metadata upload...")

    if json_path and context.config.get("save_derivatives"):
        try:
            dest = context.output_dir / (str(stem) + "_mriqc.json")
            shutil.copyfile(json_path, dest)
        except Exception as e:
            log.exception("Unable to save derivative JSON file. Skipping...")

    # Get path to HTML report
    try:
        html_path = next(tmp_dir.glob("*.html"))
    except Exception as e:
        html_path = None
        log.exception("Unable to find html path in output")

    # Optionally remove rating widget from HTML report
    if not context.config.get("include_rating_widget") and html_path:
        try:
            log.info("Removing rating widget")
            remove_rate_widget(html_path)
        except Exception as e:
            log.exception("Error removing rating widget from html report. Skipping...")

    if html_path:
        # Get path to figure directory
        try:
            figs_dir = next(tmp_dir.glob("*/**/figures/*.svg")).parent
        except Exception as e:
            figs_dir = None
            log.exception(
                "Unable to find directory of figures. Skipping report saving..."
            )

        if figs_dir:
            try:
                # Zip HTML report and save
                zip_path = zip_html_with_svg(html_path, figs_dir)
                # Save HTML report to gear output folder
                dest = context.output_dir / (str(stem) + "_mriqc.qa.html.zip")
                shutil.copyfile(zip_path, dest)
            except Exception as e:
                log.exception("Error copying zipping html report. Skipping...")

    # Remove mriqc temp directory
    try:
        shutil.rmtree(tmp_dir)
    except Exception as e:
        log.exception("Failed to delete temporary output directory...")

    # Get a list of the files in the output directory
    if output_files := os.listdir(context.output_dir):
        log.info(f"Wrote: {output_files}")
    else:
        log.error("No results written to output directory")
