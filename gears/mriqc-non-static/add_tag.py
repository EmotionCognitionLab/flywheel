#!/usr/bin/env python
"""This is a stub that will eventally expand to be the entire gear.

For now, it will just add a tag to the input file.
"""

"""The run script"""
import logging
import sys

import flywheel
from flywheel_gear_toolkit import GearToolkitContext

log = logging.getLogger(__name__)


# This function mainly parses gear_context's config.json file and returns relevant
# inputs and options.
def parse_config(
    gear_context: GearToolkitContext,
) -> (bool, str, flywheel.FileEntry):
    """Parse the config.json file.

    TODO: This may evolve with additional requirements.

    Returns:
        bool: debug parameter
    """

    debug = gear_context.config.get("debug")
    add_tag = gear_context.config.get("tag")
    input_nifti = gear_context.get_input("nifti")
    # with open(gear_context.get_input_path(""), "r") as text_file:
    #     text = " ".join(text_file.readlines())

    return debug, add_tag, input_nifti


def add_tag_to_file(context: GearToolkitContext, input_file: dict, tag: str) -> None:
    """Adds a tag to a file entry"""
    parent = context.client.get(input_file["hierarchy"]["id"])

    file_obj = parent.get_file(input_file["location"]["name"])
    if tag not in file_obj.tags:
        file_obj.add_tag(tag)


def main(context: GearToolkitContext) -> None:  # pragma: no cover
    """Parses config and run"""

    _, add_tag, input_nifti = parse_config(context)
    try:
        add_tag_to_file(context, input_nifti, add_tag)
    except Exception as exc:
        log.exception(exc)
        e_code = 1
        sys.exit(e_code)

    e_code = 0
    # e_code = run(context)

    # Exit the python script (and thus the container) with the exit code
    sys.exit(e_code)


if __name__ == "__main__":  # pragma: no cover
    # Get access to gear config, inputs, and sdk client if enabled.
    with GearToolkitContext() as gear_context:
        # Initialize logging
        gear_context.init_logging()

        # Pass the gear context into main function defined above.
        main(gear_context)
