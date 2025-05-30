"""Parser module to parse gear config.json."""
import logging
import re
import typing as t
from pathlib import Path

from flywheel_gear_toolkit import GearToolkitContext
from fw_utils import attrify

from fw_gear_mriqc.utils import true_stem

log = logging.getLogger(__name__)


def parse_config(
    gear_context: GearToolkitContext,
) -> t.Tuple[Path, str, bool, dict]:
    """Parse config.json and filepath to determine measurement type and optional
    command line arguments to mriqc

    Args:
        gear_context: GearToolkitContext object
    Returns:
        nifti_path (Path): Path to nifit file
        config_measurement (str): Measurement type, one of ["functional", "t1", "t2"]
        bids_compliant (bool): Whether nifti_path is BIDS compliant (if so,
                                    nifti_path is used to determine measurement type)
        opts (dict): Dictionary contaning optional arguments to mriqc and
                                    optional processing steps
    """

    config = attrify(gear_context.config)
    debug = config.debug
    config_measurement = config.measurement.lower()
    nifti_path = Path(gear_context.get_input_path("nifti"))
    work_dir = Path(gear_context.work_dir)
    output_dir = Path(gear_context.output_dir)

    log.info(nifti_path)

    ## VALIDATE INPUT DATA
    if not nifti_path.exists() or ".nii" not in nifti_path.suffixes:
        raise FileNotFoundError(f"Nifti file not found at {nifti_path}")

    ## CHECK FOR BIDS COMPLIANCE

    bids_func_re = re.compile(
        "sub-[0-9a-zA-Z]+(_ses-[0-9a-zA-Z]+)?_"
        "task-[0-9a-zA-Z]+(_acq-[0-9a-zA-Z]+)?"
        "(_ce-[0-9a-zA-Z]+)?(_rec-[0-9a-zA-Z]+)?"
        "(_dir-[0-9a-zA-Z]+)?(_run-[0-9]+)?"
        "(_echo-[0-9]+)?(_part-[0-9a-zA-Z]+)?"
        "(_echo-[0-9]+)?_bold"
    )
    bids_anat_re = re.compile(
        "sub-[0-9a-zA-Z]+(_ses-[0-9a-zA-Z]+)?"
        "(_acq-[0-9a-zA-Z]+)?(_ce-[0-9a-zA-Z]"
        "+)?(_rec-[0-9a-zA-Z]+)?(_run-[0-9]+)"
        "?(_part-[0-9a-zA-Z]+)?_(T1w|T2w)"
    )
    # Check if filepath matches bids funtional format
    if match := re.search(bids_func_re, str(nifti_path)):
        config_measurement = "functional"
    # Check if filepath matches bids anatomical format
    elif match := re.search(bids_anat_re, str(nifti_path)):
        anat_map = {"T1w": "t1", "T2w": "t2"}

        config_measurement = anat_map[str(true_stem(nifti_path)).split("_")[-1]]

    # If BIDS compliant
    if match:
        bids_compliant = True
        # If filepath is not identical to partial regex match, use match as filepath
        if nifti_path != match.group():
            partial_fname = Path(match.group()).with_suffix(
                "".join(nifti_path.suffixes)
            )
            log.info(
                f"Using partial filename: {(nifti_path:= nifti_path.parent / partial_fname)}"
            )
        log.info(f"Input filename is in BIDS format for a {config_measurement} image")
    # else not BIDS compliant
    else:
        bids_compliant = False
        log.info("Input filename is not in BIDS format. Detecting measurement...")

        if config_measurement == "auto-detect":
            log.info("Auto-detecting input file measurement")
            try:
                input_dict = attrify(gear_context.get_input("nifti"))
                intent = input_dict.object.classification.Intent[0]
                measurement = input_dict.object.classification.Measurement[0]
            except AttributeError:
                log.error(
                    "Unable to access Intent and Measurement attributes needed\
                           to auto-detect measurement."
                )
                raise RuntimeError(
                    "Unable to access Intent and Measurement attributes needed\
                                    to auto-detect measurement."
                )

            if intent == "Functional":
                config_measurement = intent.lower()
            elif (intent == "Structural") and (measurement in ["T1", "T2"]):
                config_measurement = measurement.lower()
            else:
                log.error(
                    "Auto-detected measurement is not compatible with algorithm. MRIQC algorithm will not run - nothing to do."
                )
                raise RuntimeError(
                    "Auto-detected measurement is not compatible with algorithm. MRIQC algorithm will not run - nothing to do."
                )
        else:
            log.info(f"File measurement indicated by user: {config_measurement}")

    if config_measurement not in ["functional", "t1", "t2"]:
        log.error(
            f"MRIQC algorithm will not run - input file measurement '{config_measurement}' is not correct"
        )
        raise RuntimeError(
            f"MRIQC algorithm will not run - input file measurement '{config_measurement}' is not correct"
        )

    # Build dictionary of gear args

    gear_args = {
        "nifti_path": nifti_path,
        "measurement": config_measurement,
        "bids_compliant": bids_compliant,
        "work_dir": work_dir,
        "output_dir": output_dir,
        "verbose_reports": config.verbose_reports,
        "include_rating_widget": config.include_rating_widget,
        "tag": config.tag,
    }

    return debug, gear_args
