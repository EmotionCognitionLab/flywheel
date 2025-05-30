#!/usr/bin/env python
"""The run script"""
import logging
import sys

from flywheel_gear_toolkit import GearToolkitContext

# This design with a separate main and parser module
# allows the gear to be publishable and the main interfaces
# to it can then be imported in another project which enables
# chaining multiple gears together.
from fw_gear_mriqc.main import cleanup, run
from fw_gear_mriqc.parser import parse_config

# The run.py should be as minimal as possible.
# The gear is split up into 2 main components. The run.py file which is executed
# when the container runs. The run.py file then imports the rest of the gear as a
# module.


log = logging.getLogger(__name__)


def main(context: GearToolkitContext) -> None:  # pragma: no cover
    """Parses gear config and run"""

    # Call parse_config to extract the args, kwargs from the context
    # (e.g. config.json).

    debug, gear_args = parse_config(context)
    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # Pass the args, kwargs to fw_gear_mriqc.main.run function to execute
    # the main functionality of the gear.
    e_code = run(gear_args)

    if e_code == 0:
        cleanup(context)

    # Exit the python script (and thus the container) with the exit
    # code returned by example_gear.main.run function.
    sys.exit(e_code)


# Only execute if file is run as main, not when imported by another module
if __name__ == "__main__":  # pragma: no cover
    # Get access to gear config, inputs, and sdk client if enabled.
    with GearToolkitContext() as gear_context:
        # Initialize logging, set logging level based on `debug` configuration
        # key in gear config.
        gear_context.init_logging()

        # Pass the gear context into main function defined above.
        main(gear_context)
